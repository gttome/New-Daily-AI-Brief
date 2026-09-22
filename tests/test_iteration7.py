from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.evaluation import (
    EvaluationBoundaryFailure,
    PostPublicationEvaluationError,
    PostPublicationEvaluationPipeline,
)
from new_daily_ai_brief.store import CanonicalStore, digest, semantic_digest


class Iteration7PostPublicationEvaluationTest(unittest.TestCase):
    DATE = "2026-09-22"

    LOCKED_ITERATION1_6 = (
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
    )

    def lock_iteration6(self, root: str, edition_date: str = DATE, mode: str = "synthetic"):
        validation = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            validation_only=True,
        )
        self.assertEqual(validation["current_state"], "Validating")
        rendered = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            render_only=True,
        )
        self.assertEqual(rendered["current_state"], "Validating")
        released = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            release_only=True,
        )
        self.assertEqual(released["current_state"], "LiveVerified")
        self.assertEqual(released["completion_status"], "shadow_live_verified")
        engine = RunEngine(root, edition_date, mode=mode, evaluation_only=True)
        return released, engine

    def evaluate_iteration7(
        self,
        root: str,
        edition_date: str = DATE,
        mode: str = "synthetic",
        evaluation_fixture_root: str | Path | None = None,
    ):
        baseline, baseline_engine = self.lock_iteration6(root, edition_date, mode)
        before_counts = dict(baseline["stage_executions"])
        before_digests = self.locked_digests(baseline_engine)
        run = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            evaluation_fixture_root=evaluation_fixture_root,
            evaluation_only=True,
        )
        engine = RunEngine(
            root,
            edition_date,
            mode=mode,
            evaluation_fixture_root=evaluation_fixture_root,
            evaluation_only=True,
        )
        return before_counts, before_digests, run, engine

    def locked_digests(self, engine: RunEngine):
        return {
            name: engine.store.load_artifact(name)["content_digest"]
            for name in self.LOCKED_ITERATION1_6
        }

    def assert_upstream_counts_unchanged(self, before, run):
        for stage, count in before.items():
            self.assertEqual(run["stage_executions"].get(stage), count, stage)

    def write_zero_fixture(self, root: str) -> Path:
        fixture = Path(root) / "iteration7-zero"
        fixture.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": "1.0.0",
            "evaluation_contract_version": "1.0.0",
            "evaluator_adapter_version": "fixture-book-change-v1",
            "required_counts": {"article": 6, "video": 2, "podcast": 2},
            "proposal_item_types": [],
            "shadow_only": True,
            "production_authorized": False,
        }
        (fixture / "evaluation-contract.json").write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        return fixture

    def test_exact_ten_item_evaluation_binds_locked_iteration6_release_chain(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, before_digests, run, engine = self.evaluate_iteration7(td)
            evaluation = engine.store.load_artifact("book-change-evaluation")
            data = evaluation["data"]
            bundle = engine.store.load_artifact("publication-bundle")
            manifest = engine.store.load_artifact("route-manifest")
            package = engine.store.load_artifact("release-package")
            deployment = engine.store.load_artifact("shadow-deployment")
            verification = engine.store.load_artifact("live-verification")

            self.assertEqual(run["current_state"], "PostPublicationEvaluation")
            self.assertEqual(run["completion_status"], "post_publication_evaluation_locked")
            self.assertEqual(len(data["item_evaluations"]), 10)
            self.assertEqual(data["evaluated_item_types"], ["article"] * 6 + ["video"] * 2 + ["podcast"] * 2)
            self.assertTrue(data["all_items_evaluated"])
            self.assertEqual(len(set(data["evaluated_item_ids"])), 10)
            self.assertEqual(data["bound_release"]["publication_bundle_digest"], bundle["content_digest"])
            self.assertEqual(data["bound_release"]["route_manifest_digest"], manifest["content_digest"])
            self.assertEqual(data["bound_release"]["release_package_digest"], package["content_digest"])
            self.assertEqual(data["bound_release"]["shadow_deployment_digest"], deployment["content_digest"])
            self.assertEqual(
                data["bound_release"]["shadow_deployment_identity"],
                deployment["data"]["deployment_identity"],
            )
            self.assertEqual(data["bound_release"]["live_verification_digest"], verification["content_digest"])
            self.assertEqual(self.locked_digests(engine), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, run)
            self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
            self.assertIsNone(engine.store.load_artifact("projection-watermark"))
            self.assertIsNone(engine.store.load_artifact("completion"))

    def test_standard_fixture_persists_proposal_records_with_exact_count(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.evaluate_iteration7(td)
            data = engine.store.load_artifact("book-change-evaluation")["data"]
            self.assertEqual(data["proposal_count"], 2)
            self.assertEqual(len(data["proposal_records"]), 2)
            self.assertTrue(all(item["item_type"] == "podcast" for item in data["proposal_records"]))
            self.assertEqual(
                data["proposal_count"],
                sum(x["disposition"] == "proposal_warranted" for x in data["item_evaluations"]),
            )
            self.assertEqual(data["result_semantics"], "proposals_present")
            self.assertFalse(data["missing_evaluation_is_zero"])

    def test_true_zero_is_explicit_and_distinct_from_missing_evaluation(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as fixture_td:
            fixture = self.write_zero_fixture(fixture_td)
            _, _, run, engine = self.evaluate_iteration7(td, evaluation_fixture_root=fixture)
            data = engine.store.load_artifact("book-change-evaluation")["data"]
            self.assertEqual(run["current_state"], "PostPublicationEvaluation")
            self.assertEqual(data["proposal_count"], 0)
            self.assertEqual(data["proposal_records"], [])
            self.assertTrue(data["all_items_evaluated"])
            self.assertEqual(data["result_semantics"], "true_zero")
            self.assertIn("0 proposals", data["result"])
            self.assertFalse(data["missing_evaluation_is_zero"])

    def test_deterministic_evaluation_replay_has_identical_semantic_identity(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            _, _, run_a, engine_a = self.evaluate_iteration7(a)
            _, _, run_b, engine_b = self.evaluate_iteration7(b)
            self.assertEqual(run_a["current_state"], "PostPublicationEvaluation")
            self.assertEqual(run_b["current_state"], "PostPublicationEvaluation")
            eval_a = engine_a.store.load_artifact("book-change-evaluation")
            eval_b = engine_b.store.load_artifact("book-change-evaluation")
            self.assertEqual(eval_a["content_digest"], eval_b["content_digest"])
            self.assertEqual(eval_a["data"], eval_b["data"])

    def test_targeted_one_item_failure_resumes_without_unrelated_item_rewrite(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration6(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            stories = engine.store.load_artifact("edition")["data"]["stories"]
            target = stories[3]["story_id"]

            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "PostPublicationEvaluation",
                    "synthetic_item_evaluation_failure",
                    f"evaluation:item:{target}",
                ),
                evaluation_only=True,
            )
            with self.assertRaises(EvaluationBoundaryFailure):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            state_before = failing.store.read_json(
                failing.store.run_dir / "post-publication-evaluation-state.json"
            )
            completed_before = deepcopy(state_before["evaluations"])
            self.assertEqual(len(completed_before), 3)
            self.assertNotIn(target, completed_before)
            self.assertIsNone(failing.store.load_artifact("book-change-evaluation"))

            resumed = RunEngine(td, self.DATE, evaluation_only=True)
            complete = resumed.run()
            state_after = resumed.store.read_json(
                resumed.store.run_dir / "post-publication-evaluation-state.json"
            )
            for item_id, record in completed_before.items():
                self.assertEqual(state_after["evaluations"][item_id], record)
            self.assertGreaterEqual(state_after["metrics"]["item_cache_reuse"], len(completed_before))
            self.assertEqual(state_after["metrics"]["unrelated_item_rewrites"], 0)
            self.assertEqual(complete["current_state"], "PostPublicationEvaluation")
            self.assertEqual(complete["completion_status"], "post_publication_evaluation_locked")
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, complete)
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "item_evaluation")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], f"item:{target}")

    def test_targeted_final_artifact_failure_reuses_all_item_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration6(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)

            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "PostPublicationEvaluation",
                    "synthetic_evaluation_artifact_failure",
                    "evaluation:artifact",
                ),
                evaluation_only=True,
            )
            with self.assertRaises(EvaluationBoundaryFailure):
                failing.run()
            state_before = failing.store.read_json(
                failing.store.run_dir / "post-publication-evaluation-state.json"
            )
            decisions_before = deepcopy(state_before["evaluations"])
            self.assertEqual(len(decisions_before), 10)
            self.assertIsNone(failing.store.load_artifact("book-change-evaluation"))

            resumed = RunEngine(td, self.DATE, evaluation_only=True)
            complete = resumed.run()
            state_after = resumed.store.read_json(
                resumed.store.run_dir / "post-publication-evaluation-state.json"
            )
            self.assertEqual(state_after["evaluations"], decisions_before)
            self.assertGreaterEqual(state_after["metrics"]["item_cache_reuse"], 10)
            self.assertEqual(state_after["metrics"]["unrelated_item_rewrites"], 0)
            self.assertEqual(complete["current_state"], "PostPublicationEvaluation")
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, complete)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "evaluation_artifact")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "artifact")

    def test_fail_closed_on_stale_or_corrupted_live_verification(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration6(td)
            engine = RunEngine(td, self.DATE, evaluation_only=True)
            verification = engine.store.load_artifact("live-verification")
            verification["data"]["result"] = "failed"
            verification["content_digest"] = semantic_digest(verification)
            engine.store._atomic_write(engine.store.artifact_path("live-verification"), verification)
            with self.assertRaises(EvaluationBoundaryFailure):
                engine.run()
            self.assertIsNone(engine.store.load_artifact("book-change-evaluation"))
            self.assertEqual(engine.store.load_run()["current_state"], "Recovering")

    def test_fail_closed_on_corrupted_cached_item_evaluation(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.lock_iteration6(td)
            stories = engine.store.load_artifact("edition")["data"]["stories"]
            target = stories[3]["story_id"]
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "PostPublicationEvaluation",
                    "pause_after_three_items",
                    f"evaluation:item:{target}",
                ),
                evaluation_only=True,
            )
            with self.assertRaises(EvaluationBoundaryFailure):
                failing.run()
            state = failing.store.read_json(
                failing.store.run_dir / "post-publication-evaluation-state.json"
            )
            first_id = next(iter(state["evaluations"]))
            state["evaluations"][first_id]["content_digest"] = "sha256:" + "0" * 64
            failing.store._atomic_write(
                failing.store.run_dir / "post-publication-evaluation-state.json",
                state,
            )
            resumed = RunEngine(td, self.DATE, evaluation_only=True)
            with self.assertRaises(EvaluationBoundaryFailure):
                resumed.run()

    def test_fail_closed_when_explicit_item_disposition_is_incomplete(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.lock_iteration6(td)
            stories = engine.store.load_artifact("edition")["data"]["stories"]
            target = stories[3]["story_id"]
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "PostPublicationEvaluation",
                    "pause_after_three_items",
                    f"evaluation:item:{target}",
                ),
                evaluation_only=True,
            )
            with self.assertRaises(EvaluationBoundaryFailure):
                failing.run()
            state = failing.store.read_json(
                failing.store.run_dir / "post-publication-evaluation-state.json"
            )
            first_id = next(iter(state["evaluations"]))
            data = state["evaluations"][first_id]["data"]
            data["disposition"] = "not_evaluated"
            data["proposal_warranted"] = False
            state["evaluations"][first_id]["content_digest"] = digest(data)
            failing.store._atomic_write(
                failing.store.run_dir / "post-publication-evaluation-state.json",
                state,
            )
            resumed = RunEngine(td, self.DATE, evaluation_only=True)
            with self.assertRaises(EvaluationBoundaryFailure):
                resumed.run()
            self.assertIsNone(resumed.store.load_artifact("book-change-evaluation"))

    def test_fail_closed_on_corrupted_locked_final_evaluation_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.evaluate_iteration7(td)
            artifact = engine.store.load_artifact("book-change-evaluation")
            artifact["data"]["proposal_count"] += 1
            engine.store._atomic_write(engine.store.artifact_path("book-change-evaluation"), artifact)
            resumed = RunEngine(td, self.DATE, evaluation_only=True)
            with self.assertRaises(EvaluationBoundaryFailure):
                resumed.run()

    def test_production_evaluation_adapter_remains_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store = CanonicalStore(Path(td), self.DATE, "production")
            pipeline = PostPublicationEvaluationPipeline(store, self.DATE, "production", None)
            with self.assertRaisesRegex(PostPublicationEvaluationError, "fail-closed"):
                pipeline.validate_release_chain()

    def test_evaluation_only_reuses_live_verification_without_release_reexecution(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration6(td)
            before_counts = dict(baseline["stage_executions"])
            verification_digest = engine.store.load_artifact("live-verification")["content_digest"]
            deployment_digest = engine.store.load_artifact("shadow-deployment")["content_digest"]
            run = start_daily_brief(self.DATE, state_root=td, evaluation_only=True)
            final = RunEngine(td, self.DATE, evaluation_only=True)
            self.assert_upstream_counts_unchanged(before_counts, run)
            self.assertEqual(
                final.store.load_artifact("live-verification")["content_digest"],
                verification_digest,
            )
            self.assertEqual(
                final.store.load_artifact("shadow-deployment")["content_digest"],
                deployment_digest,
            )
            self.assertNotIn("releasing:release-package", {
                key: value
                for key, value in run["stage_executions"].items()
                if value != before_counts.get(key, value)
            })
            self.assertIsNone(final.store.load_artifact("projection-watermark"))
            self.assertIsNone(final.store.load_artifact("completion"))

    def test_three_consecutive_shadow_evaluation_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                baseline, engine = self.lock_iteration6(td, edition_date, mode="shadow")
                before_counts = dict(baseline["stage_executions"])
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    evaluation_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow", evaluation_only=True)
                evaluation = final.store.load_artifact("book-change-evaluation")
                data = evaluation["data"]
                self.assertEqual(run["current_state"], "PostPublicationEvaluation")
                self.assertEqual(run["completion_status"], "post_publication_evaluation_locked")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(len(data["item_evaluations"]), 10)
                self.assertTrue(data["all_items_evaluated"])
                self.assertEqual(data["proposal_count"], len(data["proposal_records"]))
                self.assertEqual(self.locked_digests(final), before_digests)
                self.assert_upstream_counts_unchanged(before_counts, run)
                self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
                self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
                self.assertIsNone(final.store.load_artifact("projection-watermark"))
                self.assertIsNone(final.store.load_artifact("completion"))
                observed.append(evaluation["content_digest"])
        self.assertEqual(len(observed), 3)

    def test_iteration7_contract_schema_and_fixture_are_versioned(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads(
            (root / "fixtures" / "iteration7" / "evaluation-contract.json").read_text()
        )
        self.assertEqual(contract["evaluation_contract_version"], "1.0.0")
        self.assertEqual(contract["evaluator_adapter_version"], "fixture-book-change-v1")
        self.assertEqual(contract["required_counts"], {"article": 6, "video": 2, "podcast": 2})
        self.assertTrue(contract["shadow_only"])
        self.assertFalse(contract["production_authorized"])
        schema = json.loads((root / "schemas" / "book-change-evaluation.schema.json").read_text())
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
