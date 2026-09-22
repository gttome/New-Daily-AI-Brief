from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.evaluation import EvaluationBoundaryFailure
from new_daily_ai_brief.operations import (
    OperationsBoundaryFailure,
    OperationsReconciliationError,
    OperationsReconciliationPipeline,
    projection_currentness,
)
from new_daily_ai_brief.store import CanonicalStore, semantic_digest


class Iteration8OperationsReconciliationTest(unittest.TestCase):
    DATE = "2026-09-22"

    LOCKED_ITERATION1_7 = (
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
        "release-package",
        "shadow-deployment",
        "live-verification",
        "book-change-evaluation",
    )

    def lock_iteration7(self, root: str, edition_date: str = DATE, mode: str = "synthetic"):
        validation = start_daily_brief(edition_date, mode=mode, state_root=root, validation_only=True)
        self.assertEqual(validation["current_state"], "Validating")
        rendered = start_daily_brief(edition_date, mode=mode, state_root=root, render_only=True)
        self.assertEqual(rendered["current_state"], "Validating")
        released = start_daily_brief(edition_date, mode=mode, state_root=root, release_only=True)
        self.assertEqual(released["current_state"], "LiveVerified")
        evaluated = start_daily_brief(edition_date, mode=mode, state_root=root, evaluation_only=True)
        self.assertEqual(evaluated["current_state"], "PostPublicationEvaluation")
        self.assertEqual(evaluated["completion_status"], "post_publication_evaluation_locked")
        return evaluated, RunEngine(root, edition_date, mode=mode, reconcile_only=True)

    def locked_digests(self, engine: RunEngine):
        return {
            name: engine.store.load_artifact(name)["content_digest"]
            for name in self.LOCKED_ITERATION1_7
        }

    def reconcile(
        self,
        root: str,
        edition_date: str = DATE,
        mode: str = "synthetic",
    ):
        baseline, engine = self.lock_iteration7(root, edition_date, mode)
        before_counts = dict(baseline["stage_executions"])
        before_digests = self.locked_digests(engine)
        run = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            reconcile_only=True,
        )
        final = RunEngine(root, edition_date, mode=mode, reconcile_only=True)
        return before_counts, before_digests, run, final

    def assert_upstream_counts_unchanged(self, before, run):
        for stage, count in before.items():
            self.assertEqual(run["stage_executions"].get(stage), count, stage)

    def test_projection_represents_complete_locked_chain_and_stops_at_operations_reconciled(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, before_digests, run, engine = self.reconcile(td)
            projection = engine.store.load_artifact("command-center-projection")
            watermark = engine.store.load_artifact("projection-watermark")
            receipt = engine.store.read_json(
                engine.store.run_dir / "iteration8-shadow-command-center" / "projection-receipt.json"
            )
            data = projection["data"]
            edition = engine.store.load_artifact("edition")["data"]
            media = engine.store.load_artifact("media")["data"]
            watch = engine.store.load_artifact("watchlist")["data"]
            bridges = engine.store.load_artifact("book-bridges")["data"]["decisions"]
            images = engine.store.load_artifact("images")["data"]["images"]
            evaluation = engine.store.load_artifact("book-change-evaluation")

            self.assertEqual(run["current_state"], "OperationsReconciled")
            self.assertEqual(run["completion_status"], "operations_reconciled_locked")
            self.assertEqual(len(data["stories"]), 6)
            self.assertEqual(
                [x["story_id"] for x in data["stories"]],
                [x["story_id"] for x in edition["stories"]],
            )
            self.assertEqual(sorted(data["category_allocation"].values()), [2, 2, 2])
            self.assertEqual(data["agent_skills_count"], 1)
            self.assertEqual(
                [x["media_id"] for x in data["media"]["videos"]],
                [x["media_id"] for x in media["videos"]],
            )
            self.assertEqual(
                [x["media_id"] for x in data["media"]["podcasts"]],
                [x["media_id"] for x in media["podcasts"]],
            )
            self.assertEqual(data["watchlist"]["counts"], watch["counts"])
            self.assertEqual(data["book_bridges"], bridges)
            self.assertEqual(
                data["image_bindings"],
                [
                    {
                        "story_id": x["story_id"],
                        "image_id": x["image_id"],
                        "binary_digest": x["binary_digest"],
                    }
                    for x in images
                ],
            )
            self.assertEqual(data["rating_contract"]["contract_version"], "five-star-v1")
            self.assertIsNone(data["rating_contract"]["stored_rating_values"])
            self.assertFalse(data["rating_contract"]["fabricated_rating_values"])
            self.assertEqual(data["book_change_evaluation"]["explicit_item_evaluation_count"], 10)
            self.assertEqual(
                data["book_change_evaluation"]["evaluated_item_ids"],
                evaluation["data"]["evaluated_item_ids"],
            )
            self.assertEqual(
                data["book_change_evaluation"]["proposal_count"],
                len(evaluation["data"]["proposal_records"]),
            )
            self.assertEqual(
                set(data["bindings"]),
                set(self.LOCKED_ITERATION1_7),
            )
            self.assertEqual(
                watermark["data"]["projection_payload_digest"],
                projection["content_digest"],
            )
            self.assertEqual(projection_currentness(watermark, projection, receipt)["status"], "current")
            self.assertIsNone(engine.store.load_artifact("completion"))
            self.assertEqual(self.locked_digests(engine), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, run)
            self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)

    def test_deterministic_projection_and_watermark_replay_across_fresh_engines(self):
        observed = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as td:
                _, _, run, engine = self.reconcile(td)
                projection = engine.store.load_artifact("command-center-projection")
                watermark = engine.store.load_artifact("projection-watermark")
                observed.append(
                    (
                        projection["content_digest"],
                        deepcopy(projection["data"]),
                        watermark["content_digest"],
                        deepcopy(watermark["data"]),
                    )
                )
                replay = start_daily_brief(self.DATE, state_root=td, reconcile_only=True)
                self.assertEqual(replay["current_state"], "OperationsReconciled")
                self.assertEqual(
                    engine.store.load_artifact("command-center-projection")["content_digest"],
                    projection["content_digest"],
                )
        self.assertEqual(observed[0], observed[1])

    def test_targeted_shadow_projection_failure_recovers_without_upstream_rework(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration7(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "OperationsReconciled",
                    "synthetic_shadow_projection_failure",
                    "operations:shadow_projection",
                ),
                reconcile_only=True,
            )
            with self.assertRaises(OperationsBoundaryFailure):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            projection = failing.store.load_artifact("command-center-projection")
            self.assertIsNotNone(projection)
            self.assertIsNone(failing.store.load_artifact("projection-watermark"))
            self.assertFalse(
                (failing.store.run_dir / "iteration8-shadow-command-center" / "projection.json").exists()
            )

            resumed = RunEngine(td, self.DATE, reconcile_only=True)
            complete = resumed.run()
            state = resumed.store.read_json(resumed.store.run_dir / "iteration8-operations-state.json")
            self.assertEqual(complete["current_state"], "OperationsReconciled")
            self.assertEqual(complete["completion_status"], "operations_reconciled_locked")
            self.assertGreaterEqual(state["metrics"]["projection_reuse"], 1)
            self.assertEqual(state["metrics"]["materialization_retries"], 1)
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, complete)
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "shadow_projection")

    def test_targeted_watermark_failure_reuses_durable_projection_and_shadow_output(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration7(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "OperationsReconciled",
                    "synthetic_projection_watermark_failure",
                    "operations:watermark",
                ),
                reconcile_only=True,
            )
            with self.assertRaises(OperationsBoundaryFailure):
                failing.run()
            projection = failing.store.load_artifact("command-center-projection")
            shadow_before = failing.store.read_json(
                failing.store.run_dir / "iteration8-shadow-command-center" / "projection.json"
            )
            receipt_before = failing.store.read_json(
                failing.store.run_dir / "iteration8-shadow-command-center" / "projection-receipt.json"
            )
            self.assertIsNotNone(projection)
            self.assertIsNotNone(shadow_before)
            self.assertIsNone(failing.store.load_artifact("projection-watermark"))

            resumed = RunEngine(td, self.DATE, reconcile_only=True)
            complete = resumed.run()
            state = resumed.store.read_json(resumed.store.run_dir / "iteration8-operations-state.json")
            self.assertEqual(complete["current_state"], "OperationsReconciled")
            self.assertGreaterEqual(state["metrics"]["projection_reuse"], 1)
            self.assertGreaterEqual(state["metrics"]["materialization_cache_reuse"], 1)
            self.assertEqual(state["attempts"]["watermark"], 2)
            self.assertEqual(
                resumed.store.read_json(
                    resumed.store.run_dir / "iteration8-shadow-command-center" / "projection.json"
                ),
                shadow_before,
            )
            self.assertEqual(
                resumed.store.read_json(
                    resumed.store.run_dir / "iteration8-shadow-command-center" / "projection-receipt.json"
                ),
                receipt_before,
            )
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, complete)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)

    def test_fail_closed_on_stale_or_nonpassing_live_verification(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration7(td)
            engine = RunEngine(td, self.DATE, reconcile_only=True)
            verification = engine.store.load_artifact("live-verification")
            verification["data"]["result"] = "failed"
            verification["content_digest"] = semantic_digest(verification)
            engine.store._atomic_write(engine.store.artifact_path("live-verification"), verification)
            with self.assertRaises(EvaluationBoundaryFailure):
                engine.run()
            self.assertIsNone(engine.store.load_artifact("command-center-projection"))
            self.assertEqual(engine.store.load_run()["current_state"], "Recovering")

    def test_fail_closed_on_incomplete_iteration7_evaluation(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration7(td)
            engine = RunEngine(td, self.DATE, reconcile_only=True)
            evaluation = engine.store.load_artifact("book-change-evaluation")
            evaluation["data"]["item_evaluations"] = evaluation["data"]["item_evaluations"][:-1]
            evaluation["data"]["evaluated_item_ids"] = evaluation["data"]["evaluated_item_ids"][:-1]
            evaluation["content_digest"] = semantic_digest(evaluation)
            engine.store._atomic_write(engine.store.artifact_path("book-change-evaluation"), evaluation)
            with self.assertRaises(EvaluationBoundaryFailure):
                engine.run()
            self.assertIsNone(engine.store.load_artifact("command-center-projection"))

    def test_fail_closed_on_projection_payload_mismatch_even_with_recomputed_digest(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.reconcile(td)
            projection = engine.store.load_artifact("command-center-projection")
            projection["data"]["stories"][0]["story_id"] = "corrupted-story"
            projection["content_digest"] = semantic_digest(projection)
            engine.store._atomic_write(engine.store.artifact_path("command-center-projection"), projection)
            resumed = RunEngine(td, self.DATE, reconcile_only=True)
            with self.assertRaises(OperationsBoundaryFailure):
                resumed.run()
            self.assertEqual(resumed.store.load_run()["current_state"], "Recovering")

    def test_fail_closed_on_corrupted_shadow_projection(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.reconcile(td)
            output_path = engine.store.run_dir / "iteration8-shadow-command-center" / "projection.json"
            output = engine.store.read_json(output_path)
            output["bounded_lifecycle"]["completion_status"] = "corrupted"
            engine.store._atomic_write(output_path, output)
            resumed = RunEngine(td, self.DATE, reconcile_only=True)
            with self.assertRaises(OperationsBoundaryFailure):
                resumed.run()
            self.assertEqual(resumed.store.load_run()["current_state"], "Recovering")

    def test_fail_closed_on_stale_projection_watermark(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.reconcile(td)
            watermark = engine.store.load_artifact("projection-watermark")
            watermark["data"]["canonical_chain_digest"] = "sha256:" + "0" * 64
            watermark["content_digest"] = semantic_digest(watermark)
            engine.store._atomic_write(engine.store.artifact_path("projection-watermark"), watermark)
            resumed = RunEngine(td, self.DATE, reconcile_only=True)
            with self.assertRaises(OperationsBoundaryFailure):
                resumed.run()
            self.assertEqual(resumed.store.load_run()["current_state"], "Recovering")

    def test_currentness_semantics_distinguish_current_stale_mismatched_and_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.reconcile(td)
            projection = engine.store.load_artifact("command-center-projection")
            watermark = engine.store.load_artifact("projection-watermark")
            receipt = engine.store.read_json(
                engine.store.run_dir / "iteration8-shadow-command-center" / "projection-receipt.json"
            )
            self.assertEqual(projection_currentness(watermark, projection, receipt)["status"], "current")
            stale = deepcopy(projection)
            stale["data"]["canonical_chain_digest"] = "sha256:" + "1" * 64
            self.assertEqual(projection_currentness(watermark, stale, receipt)["status"], "stale")
            mismatch = deepcopy(receipt)
            mismatch["output_digest"] = "sha256:" + "2" * 64
            self.assertEqual(projection_currentness(watermark, projection, mismatch)["status"], "mismatched")
            self.assertEqual(projection_currentness(None, projection, receipt)["status"], "incomplete")

    def test_production_private_live_projection_adapter_remains_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store = CanonicalStore(Path(td), self.DATE, "production")
            pipeline = OperationsReconciliationPipeline(store, self.DATE, "production", None)
            with self.assertRaisesRegex(OperationsReconciliationError, "fail-closed"):
                pipeline.build_projection()

    def test_three_consecutive_shadow_reconcile_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                baseline, engine = self.lock_iteration7(td, edition_date, mode="shadow")
                before_counts = dict(baseline["stage_executions"])
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    reconcile_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow", reconcile_only=True)
                projection = final.store.load_artifact("command-center-projection")
                watermark = final.store.load_artifact("projection-watermark")
                receipt = final.store.read_json(
                    final.store.run_dir / "iteration8-shadow-command-center" / "projection-receipt.json"
                )
                self.assertEqual(run["current_state"], "OperationsReconciled")
                self.assertEqual(run["completion_status"], "operations_reconciled_locked")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(len(projection["data"]["stories"]), 6)
                self.assertEqual(
                    projection["data"]["book_change_evaluation"]["explicit_item_evaluation_count"],
                    10,
                )
                self.assertEqual(projection_currentness(watermark, projection, receipt)["status"], "current")
                self.assertIsNone(final.store.load_artifact("completion"))
                self.assertEqual(self.locked_digests(final), before_digests)
                self.assert_upstream_counts_unchanged(before_counts, run)
                self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
                self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
                observed.append(projection["content_digest"])
        self.assertEqual(len(observed), 3)

    def test_iteration8_contract_schema_and_filesystem_target_are_versioned(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads(
            (root / "fixtures" / "iteration8" / "projection-contract.json").read_text()
        )
        schema = json.loads(
            (root / "schemas" / "command-center-projection.schema.json").read_text()
        )
        self.assertEqual(contract["projection_contract_version"], "1.0.0")
        self.assertEqual(contract["projection_adapter_version"], "fixture-filesystem-shadow-v1")
        self.assertEqual(contract["target"], "isolated_fixture_filesystem_shadow")
        self.assertTrue(contract["shadow_only"])
        self.assertFalse(contract["production_authorized"])
        self.assertEqual(schema["properties"]["artifact_type"]["const"], "command-center-projection")


if __name__ == "__main__":
    unittest.main()
