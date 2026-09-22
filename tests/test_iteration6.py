from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.release import (
    ReleaseBoundaryFailure,
    ShadowReleaseError,
    ShadowReleasePipeline,
)
from new_daily_ai_brief.store import CanonicalStore, semantic_digest


class Iteration6ShadowReleaseTest(unittest.TestCase):
    DATE = "2026-09-22"

    LOCKED_ITERATION1_5 = (
        "discovery",
        "edition",
        "rating-contract",
        "media",
        "watchlist",
        "book-bridges",
        "images",
        "publication-bundle",
        "reader-render",
        "route-manifest",
    )

    def lock_iteration5(self, root: str, edition_date: str = DATE, mode: str = "synthetic"):
        validation = start_daily_brief(edition_date, mode=mode, state_root=root, validation_only=True)
        self.assertEqual(validation["current_state"], "Validating")
        self.assertEqual(validation["completion_status"], "validation_locked")
        rendered = start_daily_brief(edition_date, mode=mode, state_root=root, render_only=True)
        self.assertEqual(rendered["current_state"], "Validating")
        self.assertEqual(rendered["completion_status"], "render_locked")
        engine = RunEngine(root, edition_date, mode=mode, release_only=True)
        self.assertEqual(
            engine.store.load_artifact("route-manifest")["data"]["validation_result"],
            "passed",
        )
        return rendered, engine

    def release_iteration6(self, root: str, edition_date: str = DATE):
        baseline, baseline_engine = self.lock_iteration5(root, edition_date)
        before_counts = dict(baseline["stage_executions"])
        before_digests = self.locked_digests(baseline_engine)
        run = start_daily_brief(edition_date, state_root=root, release_only=True)
        engine = RunEngine(root, edition_date, release_only=True)
        return before_counts, before_digests, run, engine

    def locked_digests(self, engine: RunEngine):
        return {
            name: engine.store.load_artifact(name)["content_digest"]
            for name in self.LOCKED_ITERATION1_5
        }

    def assert_locked_counts_unchanged(self, before, run):
        for stage, count in before.items():
            self.assertEqual(run["stage_executions"].get(stage), count, stage)

    def test_shadow_release_preserves_exact_route_and_semantic_parity(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, before_digests, run, engine = self.release_iteration6(td)
            package = engine.store.load_artifact("release-package")
            deployment = engine.store.load_artifact("shadow-deployment")
            verification = engine.store.load_artifact("live-verification")
            manifest = engine.store.load_artifact("route-manifest")

            self.assertEqual(run["current_state"], "LiveVerified")
            self.assertEqual(run["completion_status"], "shadow_live_verified")
            self.assertEqual(package["data"]["route_manifest_digest"], manifest["content_digest"])
            self.assertEqual(package["data"]["required_output_count"], 11)
            self.assertEqual(len(package["data"]["routes"]), 11)
            self.assertTrue(package["data"]["shadow_only"])
            self.assertFalse(package["data"]["production_authorized"])

            self.assertEqual(deployment["data"]["release_package_digest"], package["content_digest"])
            self.assertEqual(deployment["data"]["output_count"], 11)
            self.assertTrue(deployment["data"]["deployment_identity"].startswith("shadow-deploy:"))
            self.assertTrue(deployment["data"]["shadow_only"])
            self.assertFalse(deployment["data"]["production_authorized"])

            self.assertEqual(verification["data"]["verification_scope"], "shadow_offline")
            self.assertEqual(verification["data"]["result"], "passed")
            self.assertTrue(all(verification["data"]["checks"].values()))
            self.assertEqual(
                verification["data"]["checked_route_ids"],
                [item["route_id"] for item in manifest["data"]["routes"]],
            )
            self.assertEqual(self.locked_digests(engine), before_digests)
            self.assert_locked_counts_unchanged(before_counts, run)
            self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
            self.assertIsNone(engine.store.load_artifact("book-change-evaluation"))
            self.assertIsNone(engine.store.load_artifact("projection-watermark"))
            self.assertIsNone(engine.store.load_artifact("completion"))
            self.assertEqual(run["stage_receipts"]["release"]["scope"], "shadow_only")
            self.assertEqual(
                run["stage_receipts"]["live_verification"]["verification_scope"],
                "shadow_offline",
            )

            reader = engine.store.load_artifact("reader-render")["data"]
            materialized = engine.store.run_dir / "shadow-deployment-outputs"
            files = sorted(materialized.glob("*.json"))
            self.assertEqual(len(files), 11)
            by_id = {item["route_id"]: item for item in reader["routes"]}
            for output in deployment["data"]["outputs"]:
                disk = engine.store.read_json(materialized / output["file"])
                self.assertEqual(
                    disk["source_output_digest"],
                    by_id[output["route_id"]]["output_digest"],
                )
                self.assertEqual(disk["release_package_digest"], package["content_digest"])

            metrics = engine.store.read_json(engine.store.run_dir / "iteration6-metrics.json")
            self.assertEqual(metrics["shadow_deployment"]["output_completions"], 11)
            self.assertEqual(metrics["shadow_deployment"]["unrelated_output_rewrites"], 0)
            self.assertGreaterEqual(metrics["verification"]["checks"], 15)

    def test_deterministic_release_deployment_and_verification_replay(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            _, _, run_a, engine_a = self.release_iteration6(a)
            _, _, run_b, engine_b = self.release_iteration6(b)
            self.assertEqual(run_a["current_state"], "LiveVerified")
            self.assertEqual(run_b["current_state"], "LiveVerified")
            for name in ("release-package", "shadow-deployment", "live-verification"):
                self.assertEqual(
                    engine_a.store.load_artifact(name)["content_digest"],
                    engine_b.store.load_artifact(name)["content_digest"],
                    name,
                )
            self.assertEqual(
                engine_a.store.load_artifact("shadow-deployment")["data"]["deployment_identity"],
                engine_b.store.load_artifact("shadow-deployment")["data"]["deployment_identity"],
            )

    def test_targeted_release_package_failure_recovers_without_locked_reexecution(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration5(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Releasing",
                    "synthetic_release_package_failure",
                    "release:package",
                ),
                release_only=True,
            )
            with self.assertRaises(ReleaseBoundaryFailure):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            self.assertIsNone(failing.store.load_artifact("release-package"))
            self.assertIn("route-manifest", failing.store.load_incident()["retained_locks"])

            resumed = RunEngine(td, self.DATE, release_only=True)
            complete = resumed.run()
            self.assertEqual(complete["current_state"], "LiveVerified")
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_locked_counts_unchanged(before_counts, complete)
            self.assertEqual(complete["stage_executions"]["releasing:release-package"], 2)
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "release_package")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "package")

    def test_targeted_one_output_deployment_failure_reuses_completed_outputs(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration5(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            reader_routes = engine.store.load_artifact("reader-render")["data"]["routes"]
            target_route_id = reader_routes[6]["route_id"]
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Releasing",
                    "synthetic_shadow_output_failure",
                    f"release:output:{target_route_id}",
                ),
                release_only=True,
            )
            with self.assertRaises(ReleaseBoundaryFailure):
                failing.run()
            state_before = failing.store.read_json(
                failing.store.run_dir / "shadow-deployment-state.json"
            )
            completed_before = deepcopy(state_before["outputs"])
            self.assertGreaterEqual(len(completed_before), 6)
            self.assertNotIn(target_route_id, completed_before)
            self.assertIsNotNone(failing.store.load_artifact("release-package"))
            self.assertIsNone(failing.store.load_artifact("shadow-deployment"))

            resumed = RunEngine(td, self.DATE, release_only=True)
            complete = resumed.run()
            state_after = resumed.store.read_json(
                resumed.store.run_dir / "shadow-deployment-state.json"
            )
            for route_id, summary in completed_before.items():
                self.assertEqual(state_after["outputs"][route_id], summary)
            self.assertGreaterEqual(
                state_after["metrics"]["output_cache_reuse"],
                len(completed_before),
            )
            self.assertEqual(state_after["metrics"]["unrelated_output_rewrites"], 0)
            self.assertEqual(
                complete["stage_executions"]["releasing:shadow-deployment"],
                2,
            )
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_locked_counts_unchanged(before_counts, complete)
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "shadow_output")
            self.assertEqual(
                incident["recovery_receipt"]["boundary_id"],
                f"output:{target_route_id}",
            )

    def test_targeted_verification_failure_recovers_without_redeployment(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration5(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Deployed",
                    "synthetic_shadow_verification_failure",
                    "release:verification",
                ),
                release_only=True,
            )
            with self.assertRaises(ReleaseBoundaryFailure):
                failing.run()
            deployment_digest = failing.store.load_artifact("shadow-deployment")["content_digest"]
            deployment_state = deepcopy(
                failing.store.read_json(failing.store.run_dir / "shadow-deployment-state.json")
            )
            self.assertIsNone(failing.store.load_artifact("live-verification"))
            self.assertEqual(failing.store.load_run()["current_state"], "Recovering")

            resumed = RunEngine(td, self.DATE, release_only=True)
            complete = resumed.run()
            self.assertEqual(complete["current_state"], "LiveVerified")
            self.assertEqual(
                resumed.store.load_artifact("shadow-deployment")["content_digest"],
                deployment_digest,
            )
            self.assertEqual(
                resumed.store.read_json(resumed.store.run_dir / "shadow-deployment-state.json")["outputs"],
                deployment_state["outputs"],
            )
            self.assertEqual(complete["stage_executions"]["releasing:release-package"], 1)
            self.assertEqual(complete["stage_executions"]["releasing:shadow-deployment"], 1)
            self.assertEqual(complete["stage_executions"]["deployed:shadow-verification"], 2)
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_locked_counts_unchanged(before_counts, complete)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "shadow_verification")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "verification")

    def test_fail_closed_on_stale_route_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration5(td)
            engine = RunEngine(td, self.DATE, release_only=True)
            manifest = engine.store.load_artifact("route-manifest")
            manifest["edition_date"] = "2026-09-20"
            manifest["content_digest"] = semantic_digest(manifest)
            engine.store._atomic_write(engine.store.artifact_path("route-manifest"), manifest)
            with self.assertRaises(ReleaseBoundaryFailure):
                engine.run()
            self.assertIsNone(engine.store.load_artifact("release-package"))

    def test_fail_closed_on_corrupted_route_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration5(td)
            engine = RunEngine(td, self.DATE, release_only=True)
            manifest = engine.store.load_artifact("route-manifest")
            manifest["data"]["validation_result"] = "failed"
            engine.store._atomic_write(engine.store.artifact_path("route-manifest"), manifest)
            with self.assertRaises(ReleaseBoundaryFailure):
                engine.run()
            self.assertIsNone(engine.store.load_artifact("release-package"))

    def test_fail_closed_on_corrupted_shadow_output(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration5(td)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Deployed",
                    "pause_before_verification",
                    "release:verification",
                ),
                release_only=True,
            )
            with self.assertRaises(ReleaseBoundaryFailure):
                failing.run()
            path = failing.store.run_dir / "shadow-deployment-outputs" / "current.json"
            record = failing.store.read_json(path)
            record["content"] += "<!-- corrupted -->"
            failing.store._atomic_write(path, record)

            resumed = RunEngine(td, self.DATE, release_only=True)
            with self.assertRaises(ReleaseBoundaryFailure):
                resumed.run()
            self.assertEqual(resumed.store.load_run()["current_state"], "Recovering")

    def test_fail_closed_on_extra_shadow_output(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration5(td)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Deployed",
                    "pause_before_verification",
                    "release:verification",
                ),
                release_only=True,
            )
            with self.assertRaises(ReleaseBoundaryFailure):
                failing.run()
            extra = failing.store.run_dir / "shadow-deployment-outputs" / "unexpected.json"
            failing.store._atomic_write(
                extra,
                {"schema_version": "1.0.0", "unexpected": True},
            )
            resumed = RunEngine(td, self.DATE, release_only=True)
            with self.assertRaises(ReleaseBoundaryFailure):
                resumed.run()

    def test_production_deployment_adapter_remains_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store = CanonicalStore(Path(td), self.DATE, "production")
            pipeline = ShadowReleasePipeline(store, self.DATE, "production", None)
            with self.assertRaisesRegex(ShadowReleaseError, "fail-closed"):
                pipeline.validate_release_inputs()

    def test_route_manifest_invalidation_invalidates_only_release_descendants(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.release_iteration6(td)
            upstream = {
                name: engine.store.load_artifact(name)["status"]
                for name in (
                    "discovery",
                    "edition",
                    "rating-contract",
                    "media",
                    "watchlist",
                    "book-bridges",
                    "images",
                    "publication-bundle",
                    "reader-render",
                )
            }
            changed = engine.store.invalidate("route-manifest", "synthetic_manifest_change")
            self.assertEqual(
                set(changed),
                {
                    "route-manifest",
                    "release-package",
                    "shadow-deployment",
                    "live-verification",
                },
            )
            for name, status in upstream.items():
                self.assertEqual(status, "locked")
                self.assertEqual(engine.store.load_artifact(name)["status"], "locked")

    def test_three_consecutive_shadow_release_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                baseline, engine = self.lock_iteration5(td, edition_date, mode="shadow")
                before_counts = dict(baseline["stage_executions"])
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    release_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow", release_only=True)
                package = final.store.load_artifact("release-package")
                deployment = final.store.load_artifact("shadow-deployment")
                verification = final.store.load_artifact("live-verification")
                self.assertEqual(run["current_state"], "LiveVerified")
                self.assertEqual(run["completion_status"], "shadow_live_verified")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(package["data"]["required_output_count"], 11)
                self.assertEqual(deployment["data"]["output_count"], 11)
                self.assertEqual(verification["data"]["result"], "passed")
                self.assertEqual(verification["data"]["verification_scope"], "shadow_offline")
                self.assertTrue(all(verification["data"]["checks"].values()))
                self.assertFalse(package["data"]["production_authorized"])
                self.assertTrue(package["data"]["shadow_only"])
                self.assertEqual(self.locked_digests(final), before_digests)
                self.assert_locked_counts_unchanged(before_counts, run)
                self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
                self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
                self.assertIsNone(final.store.load_artifact("book-change-evaluation"))
                self.assertIsNone(final.store.load_artifact("projection-watermark"))
                self.assertIsNone(final.store.load_artifact("completion"))
                observed.append(
                    {
                        "edition_date": edition_date,
                        "package_digest": package["content_digest"],
                        "deployment_identity": deployment["data"]["deployment_identity"],
                        "verification_digest": verification["content_digest"],
                    }
                )
        self.assertEqual(len(observed), 3)

    def test_iteration6_contract_schemas_exist_and_are_versioned(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads(
            (root / "fixtures" / "iteration6" / "release-contract.json").read_text()
        )
        self.assertEqual(contract["release_package_contract_version"], "1.0.0")
        self.assertEqual(contract["deployment_adapter_version"], "shadow-filesystem-v1")
        self.assertEqual(contract["verification_scope"], "shadow_offline")
        self.assertTrue(contract["shadow_only"])
        self.assertFalse(contract["production_authorized"])
        for name in ("release-package", "shadow-deployment", "live-verification"):
            doc = json.loads((root / "schemas" / f"{name}.schema.json").read_text())
            self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
