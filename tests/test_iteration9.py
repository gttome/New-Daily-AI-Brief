from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.completion import (
    CompletionBoundaryFailure,
    CompletionError,
    FinalCompletionPipeline,
)
from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.operations import OperationsBoundaryFailure
from new_daily_ai_brief.store import CanonicalStore, semantic_digest


class Iteration9FinalCompletionTest(unittest.TestCase):
    DATE = "2026-09-22"
    LOCKED_ITERATION1_8 = (
        "discovery", "edition", "rating-contract", "media", "watchlist",
        "book-bridges", "images", "publication-bundle", "reader-render",
        "route-manifest", "release-package", "shadow-deployment",
        "live-verification", "book-change-evaluation",
        "command-center-projection", "projection-watermark",
    )

    def lock_iteration8(self, root: str, edition_date: str = DATE, mode: str = "synthetic"):
        validation = start_daily_brief(
            edition_date, mode=mode, state_root=root, validation_only=True
        )
        self.assertEqual(validation["current_state"], "Validating")
        rendered = start_daily_brief(
            edition_date, mode=mode, state_root=root, render_only=True
        )
        self.assertEqual(rendered["current_state"], "Validating")
        released = start_daily_brief(
            edition_date, mode=mode, state_root=root, release_only=True
        )
        self.assertEqual(released["current_state"], "LiveVerified")
        evaluated = start_daily_brief(
            edition_date, mode=mode, state_root=root, evaluation_only=True
        )
        self.assertEqual(evaluated["current_state"], "PostPublicationEvaluation")
        reconciled = start_daily_brief(
            edition_date, mode=mode, state_root=root, reconcile_only=True
        )
        self.assertEqual(reconciled["current_state"], "OperationsReconciled")
        self.assertEqual(
            reconciled["completion_status"], "operations_reconciled_locked"
        )
        return reconciled, RunEngine(
            root, edition_date, mode=mode, completion_only=True
        )

    def locked_digests(self, engine: RunEngine):
        return {
            name: engine.store.load_artifact(name)["content_digest"]
            for name in self.LOCKED_ITERATION1_8
        }

    def assert_upstream_counts_unchanged(self, before, run):
        for stage, count in before.items():
            self.assertEqual(run["stage_executions"].get(stage), count, stage)

    def complete(self, root: str, edition_date: str = DATE, mode: str = "synthetic"):
        baseline, engine = self.lock_iteration8(root, edition_date, mode)
        before_counts = dict(baseline["stage_executions"])
        before_digests = self.locked_digests(engine)
        run = start_daily_brief(
            edition_date, mode=mode, state_root=root, completion_only=True
        )
        final = RunEngine(root, edition_date, mode=mode, completion_only=True)
        return before_counts, before_digests, run, final

    def test_completion_binds_entire_locked_chain_and_is_nonproduction(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, before_digests, run, engine = self.complete(td)
            completion = engine.store.load_artifact("completion")
            receipt = engine.store.read_json(
                engine.store.run_dir / "iteration9-final-completion-receipt.json"
            )
            data = completion["data"]
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(run["completion_status"], "complete_locked")
            self.assertEqual(data["completion_scope"], "synthetic_shadow_validation")
            self.assertEqual(data["final_state"], "Complete")
            self.assertEqual(data["final_status"], "complete_locked")
            self.assertFalse(data["production_cutover_authorized"])
            self.assertFalse(data["legacy_decommission_authorized"])
            self.assertFalse(data["real_command_center_mutated"])
            self.assertFalse(data["public_site_mutated"])
            self.assertFalse(data["production_publication"])
            bound = set(data["complete_chain_bindings"])
            self.assertTrue(set(self.LOCKED_ITERATION1_8).issubset(bound))
            self.assertIn("shadow-projection-receipt", bound)
            self.assertIn("shadow-projection-output", bound)
            self.assertEqual(receipt["transition_count"], 1)
            self.assertEqual(run["stage_receipts"]["final_completion"], receipt)
            self.assertEqual(self.locked_digests(engine), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, run)
            self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)

    def test_deterministic_completion_replay_and_recovery_history_independent_identity(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, run, engine = self.complete(td)
            clean_digest = engine.store.load_artifact("completion")["content_digest"]
            before = deepcopy(run["stage_executions"])
            replay = start_daily_brief(
                self.DATE, state_root=td, completion_only=True
            )
            self.assertEqual(replay["current_state"], "Complete")
            self.assertEqual(replay["stage_executions"], before)
            self.assertEqual(
                engine.store.load_artifact("completion")["content_digest"],
                clean_digest,
            )

        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration8(td)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "OperationsReconciled",
                    "synthetic_completion_artifact_failure",
                    "completion:completion_artifact",
                ),
                completion_only=True,
            )
            with self.assertRaises(CompletionBoundaryFailure):
                failing.run()
            recovered = start_daily_brief(
                self.DATE, state_root=td, completion_only=True
            )
            self.assertEqual(recovered["current_state"], "Complete")
            self.assertEqual(
                RunEngine(td, self.DATE, completion_only=True)
                .store.load_artifact("completion")["content_digest"],
                clean_digest,
            )

    def test_targeted_completion_artifact_failure_recovers_with_fresh_engine(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration8(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "OperationsReconciled",
                    "synthetic_completion_artifact_failure",
                    "completion:completion_artifact",
                ),
                completion_only=True,
            )
            with self.assertRaises(CompletionBoundaryFailure):
                failing.run()
            self.assertEqual(failing.store.load_run()["current_state"], "Recovering")
            self.assertIsNone(failing.store.load_artifact("completion"))

            resumed = RunEngine(td, self.DATE, completion_only=True)
            final = resumed.run()
            state = resumed.store.read_json(
                resumed.store.run_dir / "iteration9-completion-state.json"
            )
            self.assertEqual(final["current_state"], "Complete")
            self.assertEqual(state["attempts"]["completion_artifact"], 2)
            self.assertEqual(state["metrics"]["completion_build_retries"], 1)
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, final)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(
                incident["recovery_receipt"]["boundary_id"], "completion_artifact"
            )

    def test_targeted_final_state_receipt_failure_reuses_durable_completion(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration8(td)
            before_counts = dict(baseline["stage_executions"])
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "OperationsReconciled",
                    "synthetic_final_state_receipt_failure",
                    "completion:final_state_receipt",
                ),
                completion_only=True,
            )
            with self.assertRaises(CompletionBoundaryFailure):
                failing.run()
            completion = failing.store.load_artifact("completion")
            receipt = failing.store.read_json(
                failing.store.run_dir / "iteration9-final-completion-receipt.json"
            )
            self.assertIsNotNone(completion)
            self.assertIsNotNone(receipt)
            completion_digest = completion["content_digest"]

            resumed = RunEngine(td, self.DATE, completion_only=True)
            final = resumed.run()
            state = resumed.store.read_json(
                resumed.store.run_dir / "iteration9-completion-state.json"
            )
            self.assertEqual(final["current_state"], "Complete")
            self.assertEqual(
                resumed.store.load_artifact("completion")["content_digest"],
                completion_digest,
            )
            self.assertEqual(
                resumed.store.read_json(
                    resumed.store.run_dir / "iteration9-final-completion-receipt.json"
                ),
                receipt,
            )
            self.assertEqual(state["attempts"]["final_state_receipt"], 2)
            self.assertEqual(state["metrics"]["final_transition_retries"], 1)
            self.assertGreaterEqual(state["metrics"]["final_receipt_reuse"], 1)
            self.assertEqual(self.locked_digests(resumed), before_digests)
            self.assert_upstream_counts_unchanged(before_counts, final)

    def test_fail_closed_on_stale_live_verification(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.lock_iteration8(td)
            verification = engine.store.load_artifact("live-verification")
            verification["data"]["result"] = "failed"
            verification["content_digest"] = semantic_digest(verification)
            engine.store._atomic_write(
                engine.store.artifact_path("live-verification"), verification
            )
            with self.assertRaises(OperationsBoundaryFailure):
                start_daily_brief(self.DATE, state_root=td, completion_only=True)
            self.assertIsNone(engine.store.load_artifact("completion"))

    def test_fail_closed_on_incomplete_iteration7_evaluation(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.lock_iteration8(td)
            evaluation = engine.store.load_artifact("book-change-evaluation")
            evaluation["data"]["item_evaluations"] = evaluation["data"][
                "item_evaluations"
            ][:-1]
            evaluation["content_digest"] = semantic_digest(evaluation)
            engine.store._atomic_write(
                engine.store.artifact_path("book-change-evaluation"), evaluation
            )
            with self.assertRaises(OperationsBoundaryFailure):
                start_daily_brief(self.DATE, state_root=td, completion_only=True)

    def test_fail_closed_on_corrupted_projection_or_shadow_output(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.lock_iteration8(td)
            projection = engine.store.load_artifact("command-center-projection")
            projection["data"]["stories"][0]["story_id"] = "corrupt"
            projection["content_digest"] = semantic_digest(projection)
            engine.store._atomic_write(
                engine.store.artifact_path("command-center-projection"), projection
            )
            with self.assertRaises(OperationsBoundaryFailure):
                start_daily_brief(self.DATE, state_root=td, completion_only=True)

        with tempfile.TemporaryDirectory() as td:
            _, engine = self.lock_iteration8(td)
            output_path = (
                engine.store.run_dir / "iteration8-shadow-command-center" / "projection.json"
            )
            output = engine.store.read_json(output_path)
            output["shadow_only"] = False
            engine.store._atomic_write(output_path, output)
            with self.assertRaises(OperationsBoundaryFailure):
                start_daily_brief(self.DATE, state_root=td, completion_only=True)

    def test_fail_closed_on_stale_projection_watermark(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.lock_iteration8(td)
            watermark = engine.store.load_artifact("projection-watermark")
            watermark["data"]["canonical_chain_digest"] = "sha256:" + "0" * 64
            watermark["content_digest"] = semantic_digest(watermark)
            engine.store._atomic_write(
                engine.store.artifact_path("projection-watermark"), watermark
            )
            with self.assertRaises(OperationsBoundaryFailure):
                start_daily_brief(self.DATE, state_root=td, completion_only=True)

    def test_corrupted_cached_completion_and_final_receipt_fail_closed_on_replay(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.complete(td)
            completion = engine.store.load_artifact("completion")
            completion["data"]["completion_scope"] = "corrupted"
            completion["content_digest"] = semantic_digest(completion)
            engine.store._atomic_write(
                engine.store.artifact_path("completion"), completion
            )
            with self.assertRaises(CompletionBoundaryFailure):
                start_daily_brief(self.DATE, state_root=td, completion_only=True)

        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.complete(td)
            path = engine.store.run_dir / "iteration9-final-completion-receipt.json"
            receipt = engine.store.read_json(path)
            receipt["final_status"] = "corrupted"
            engine.store._atomic_write(path, receipt)
            with self.assertRaises(CompletionBoundaryFailure):
                start_daily_brief(self.DATE, state_root=td, completion_only=True)

    def test_unsupported_contract_and_production_adapter_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration8(td)
            fixture = Path(td) / "bad-fixture"
            fixture.mkdir()
            (fixture / "completion-contract.json").write_text(
                json.dumps(
                    {
                        "schema_version": "1.0.0",
                        "completion_contract_version": "99.0.0",
                        "completion_scope": "synthetic_shadow_validation",
                        "shadow_only": True,
                        "production_authorized": False,
                        "production_cutover_authorized": False,
                        "legacy_decommission_authorized": False,
                        "real_command_center_mutation_authorized": False,
                        "public_site_mutation_authorized": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(CompletionError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    completion_fixture_root=fixture,
                    completion_only=True,
                )

        with tempfile.TemporaryDirectory() as td:
            store = CanonicalStore(Path(td), self.DATE, "production")
            pipeline = FinalCompletionPipeline(
                store, self.DATE, "production", None, None
            )
            with self.assertRaisesRegex(CompletionError, "fail-closed"):
                pipeline.build_completion({})

    def test_three_consecutive_shadow_completion_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                baseline, engine = self.lock_iteration8(
                    td, edition_date, mode="shadow"
                )
                before_counts = dict(baseline["stage_executions"])
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    completion_only=True,
                )
                final = RunEngine(
                    td, edition_date, mode="shadow", completion_only=True
                )
                completion = final.store.load_artifact("completion")
                receipt = final.store.read_json(
                    final.store.run_dir / "iteration9-final-completion-receipt.json"
                )
                self.assertEqual(run["current_state"], "Complete")
                self.assertEqual(run["completion_status"], "complete_locked")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(
                    completion["data"]["completion_scope"],
                    "synthetic_shadow_validation",
                )
                self.assertEqual(receipt["transition_count"], 1)
                self.assertFalse(completion["data"]["production_cutover_authorized"])
                self.assertFalse(completion["data"]["real_command_center_mutated"])
                self.assertFalse(completion["data"]["public_site_mutated"])
                self.assertFalse(completion["data"]["production_publication"])
                self.assertEqual(self.locked_digests(final), before_digests)
                self.assert_upstream_counts_unchanged(before_counts, run)
                self.assertEqual(
                    run["anti_rework"]["locked_stage_reexecutions"], 0
                )
                self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
                observed.append(
                    (
                        completion["content_digest"],
                        completion["data"]["completion_event_id"],
                    )
                )
        self.assertEqual(len(observed), 3)

    def test_completion_contract_and_schema_are_versioned_and_shadow_scoped(self):
        root = Path(__file__).resolve().parents[1]
        contract = json.loads(
            (root / "fixtures" / "iteration9" / "completion-contract.json").read_text()
        )
        schema = json.loads(
            (root / "schemas" / "final-completion-event.schema.json").read_text()
        )
        self.assertEqual(contract["completion_contract_version"], "1.0.0")
        self.assertEqual(
            contract["completion_scope"], "synthetic_shadow_validation"
        )
        self.assertFalse(contract["production_authorized"])
        self.assertFalse(contract["production_cutover_authorized"])
        self.assertEqual(schema["properties"]["final_state"]["const"], "Complete")
        self.assertEqual(
            schema["properties"]["final_status"]["const"], "complete_locked"
        )


if __name__ == "__main__":
    unittest.main()
