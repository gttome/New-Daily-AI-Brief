from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_rehearsal import (
    IntegrationExecutionRehearsalBoundaryFailure,
    IntegrationExecutionRehearsalError,
)
from new_daily_ai_brief.store import digest
import test_iteration14


class Iteration15IntegrationExecutionRehearsalTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration14.Iteration14IntegrationExecutionPreflightTest(
            methodName="test_current_blocked_admission_cannot_silently_become_execution_review_ready"
        )

    def fixture(self, name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration15" / name

    def make_execution_preflight(
        self,
        root: str,
        edition_date: str = DATE,
        mode: str = "synthetic",
        *,
        review_ready: bool = False,
    ):
        h = self.helper()
        _, engine = h.make_admission(
            root,
            edition_date,
            mode,
            authorization_ready=review_ready,
        )
        kwargs = {}
        if review_ready:
            fixture = h.write_fixture(Path(root) / "iteration14-review-ready", engine)
            kwargs["integration_execution_preflight_fixture_root"] = fixture
        run = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            integration_execution_preflight_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, edition_date, mode=mode)

    def locked_digests(self, engine: RunEngine):
        values = self.helper().locked_digests(engine)
        values["production-integration-execution-preflight"] = engine.store.load_artifact(
            "production-integration-execution-preflight"
        )["content_digest"]
        return values

    def write_fixture(
        self,
        root: Path,
        engine: RunEngine,
        *,
        source: str = "synthetic-rehearsal-ready",
        policy_mutator=None,
        manifest_mutator=None,
    ) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        policy = json.loads((self.fixture(source) / "rehearsal-policy.json").read_text())
        manifest = json.loads(
            (self.fixture(source) / "rehearsal-envelope-manifest.json").read_text()
        )
        plan = engine.store.load_artifact("production-integration-plan")
        if plan and manifest["evidence"]["step_selection_scope"] is not None:
            data = plan["data"]
            step_ids = [x["step_id"] for x in data["plan_steps"]]
            manifest["evidence"]["step_selection_scope"]["plan_id"] = data["plan_id"]
            manifest["evidence"]["step_selection_scope"]["plan_graph_digest"] = digest(
                data["plan_steps"]
            )
            manifest["evidence"]["step_selection_scope"]["step_ids"] = step_ids
            manifest["evidence"]["noop_policy"]["steps"] = [
                {
                    "step_id": step_id,
                    "noop": True,
                    "real_executable": False,
                    "external_execution_performed": False,
                    "production_action_authorized": False,
                }
                for step_id in step_ids
            ]
            manifest["evidence"]["dry_run_assertions"][
                "dry_run_assertion_set_digest"
            ] = digest(data["dry_run_assertion_set"])
            manifest["evidence"]["rollback_restore"][
                "rollback_boundary_set_digest"
            ] = digest(data["rollback_boundary_set"])
        if policy_mutator:
            policy_mutator(policy)
        if manifest_mutator:
            manifest_mutator(manifest)
        (root / "rehearsal-policy.json").write_text(json.dumps(policy))
        (root / "rehearsal-envelope-manifest.json").write_text(json.dumps(manifest))
        return root

    def assert_safety_flags_false(self, data):
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_private_command_center_mutated",
            "public_site_mutated",
            "production_schedule_action",
            "subscriber_delivery_changed",
            "legacy_content_migrated",
            "readers_routed_to_greenfield",
            "legacy_repository_modified",
            "incremental_paid_dependency_added",
            "lifecycle_state_changed",
        ):
            self.assertFalse(data[flag])
        self.assertEqual(data["real_integration_steps_enabled"], 0)
        self.assertEqual(data["real_integration_steps_executed"], 0)

    def test_current_blocked_execution_preflight_remains_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_execution_preflight(td)
            before_digests = self.locked_digests(engine)
            run = start_daily_brief(
                self.DATE, state_root=td, integration_execution_rehearsal_only=True
            )
            final = RunEngine(td, self.DATE)
            artifact = final.store.load_artifact(
                "production-integration-execution-rehearsal"
            )
            data = artifact["data"]
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(run["completion_status"], "complete_locked")
            self.assertEqual(data["execution_preflight_classification"], "blocked")
            self.assertEqual(data["classification"], "blocked")
            self.assertEqual(
                data["classification_reason_codes"][0],
                "ITERATION14_EXECUTION_PREFLIGHT_BLOCKED",
            )
            self.assertEqual(data["rehearsal_receipt_count"], 0)
            self.assertIsNone(data["execution_attempt_id"])
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)
            self.assert_safety_flags_false(data)

    def test_execution_review_ready_alone_is_insufficient(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_execution_preflight(td, review_ready=True)
            start_daily_brief(
                self.DATE, state_root=td, integration_execution_rehearsal_only=True
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-rehearsal"
            )["data"]
            self.assertEqual(data["execution_preflight_classification"], "execution_review_ready")
            self.assertEqual(data["classification"], "blocked")
            self.assertIn("REHEARSAL_RUNNER_CONTRACT_MISSING", data["classification_reason_codes"])
            self.assertIn("REHEARSAL_DECISION_MISSING", data["classification_reason_codes"])
            self.assertEqual(data["rehearsal_receipt_count"], 0)

    def test_separate_rehearsal_decision_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            fixture = self.write_fixture(
                Path(td) / "no-decision",
                engine,
                manifest_mutator=lambda m: m.update({"rehearsal_decision": None}),
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-rehearsal"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertIn("REHEARSAL_DECISION_MISSING", data["classification_reason_codes"])
            self.assertEqual(data["rehearsal_receipt_count"], 0)

    def test_complete_synthetic_rehearsal_has_exactly_ten_noop_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "ready", engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            final = RunEngine(td, self.DATE)
            data = final.store.load_artifact(
                "production-integration-execution-rehearsal"
            )["data"]
            plan = final.store.load_artifact("production-integration-plan")["data"]
            self.assertEqual(data["classification"], "rehearsal_complete")
            self.assertEqual(
                data["classification_reason_codes"], ["SYNTHETIC_NOOP_REHEARSAL_COMPLETE"]
            )
            self.assertEqual(data["rehearsal_decision_id"], "synthetic-rehearsal-decision-v1")
            self.assertIsNotNone(data["execution_attempt_id"])
            self.assertEqual(data["rehearsal_receipt_count"], 10)
            receipts = data["rehearsal_receipts"]
            self.assertEqual(
                [x["step_id"] for x in receipts],
                [x["step_id"] for x in plan["plan_steps"]],
            )
            self.assertEqual([x["position"] for x in receipts], list(range(1, 11)))
            for receipt in receipts:
                self.assertEqual(receipt["execution_mode"], "noop")
                self.assertEqual(receipt["evaluation_result"], "evaluated_not_executed")
                self.assertFalse(receipt["external_execution_performed"])
                self.assertFalse(receipt["real_service_contacted"])
                self.assertFalse(receipt["side_effect_performed"])
                self.assertFalse(receipt["production_action_authorized"])
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in engine.store.load_run()["stage_executions"].items():
                if stage != "complete:integration-execution-rehearsal":
                    self.assertEqual(run["stage_executions"].get(stage), count)
            self.assert_safety_flags_false(data)

    def test_exact_iteration14_and_transitive_bindings_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            fixture = self.write_fixture(Path(td) / "bindings", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            final = RunEngine(td, self.DATE)
            data = final.store.load_artifact(
                "production-integration-execution-rehearsal"
            )["data"]
            ep = final.store.load_artifact("production-integration-execution-preflight")
            admission = final.store.load_artifact("production-integration-admission")
            plan = final.store.load_artifact("production-integration-plan")
            preflight = final.store.load_artifact("production-integration-preflight")
            readiness = final.store.load_artifact("readiness-admission")
            completion = final.store.load_artifact("completion")
            self.assertEqual(data["execution_preflight_artifact_digest"], ep["content_digest"])
            self.assertEqual(data["execution_preflight_id"], ep["data"]["execution_preflight_id"])
            self.assertEqual(data["admission_artifact_digest"], admission["content_digest"])
            self.assertEqual(data["admission_id"], admission["data"]["admission_id"])
            self.assertEqual(data["plan_artifact_digest"], plan["content_digest"])
            self.assertEqual(data["plan_id"], plan["data"]["plan_id"])
            self.assertEqual(data["plan_graph_digest"], digest(plan["data"]["plan_steps"]))
            self.assertEqual(
                data["dry_run_assertion_set_digest"], digest(plan["data"]["dry_run_assertion_set"])
            )
            self.assertEqual(
                data["rollback_boundary_set_digest"], digest(plan["data"]["rollback_boundary_set"])
            )
            self.assertEqual(data["preflight_artifact_digest"], preflight["content_digest"])
            self.assertEqual(data["readiness_artifact_digest"], readiness["content_digest"])
            self.assertEqual(data["completion_artifact_digest"], completion["content_digest"])
            self.assertEqual(data["canonical_chain_digest"], completion["data"]["canonical_chain_digest"])

    def test_rehearsal_identity_and_replay_are_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            fixture = self.write_fixture(Path(td) / "replay", engine)
            kwargs = {
                "integration_execution_rehearsal_fixture_root": fixture,
                "integration_execution_rehearsal_only": True,
            }
            first = start_daily_brief(self.DATE, state_root=td, **kwargs)
            a1 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-rehearsal"
            )
            ids1 = [x["receipt_id"] for x in a1["data"]["rehearsal_receipts"]]
            counts = deepcopy(first["stage_executions"])
            second = start_daily_brief(self.DATE, state_root=td, **kwargs)
            a2 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-rehearsal"
            )
            self.assertEqual(a1["content_digest"], a2["content_digest"])
            self.assertEqual(a1["data"]["execution_rehearsal_id"], a2["data"]["execution_rehearsal_id"])
            self.assertEqual(a1["data"]["execution_attempt_id"], a2["data"]["execution_attempt_id"])
            self.assertEqual(ids1, [x["receipt_id"] for x in a2["data"]["rehearsal_receipts"]])
            self.assertEqual(second["stage_executions"], counts)
            state = RunEngine(td, self.DATE).store.read_json(
                RunEngine(td, self.DATE).store.run_dir / "iteration15-execution-rehearsal-state.json"
            )
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 10)
            self.assertGreaterEqual(state["metrics"]["artifact_reuse"], 1)

    def test_corrupted_iteration14_execution_preflight_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            artifact = engine.store.load_artifact("production-integration-execution-preflight")
            artifact["data"]["classification"] = "blocked"
            engine.store._atomic_write(
                engine.store.artifact_path("production-integration-execution-preflight"), artifact
            )
            with self.assertRaises(IntegrationExecutionRehearsalError):
                start_daily_brief(
                    self.DATE, state_root=td, integration_execution_rehearsal_only=True
                )
            self.assertIsNone(
                engine.store.load_artifact("production-integration-execution-rehearsal")
            )

    def test_unsupported_rehearsal_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            fixture = self.write_fixture(
                Path(td) / "bad-version",
                engine,
                policy_mutator=lambda p: p.update({"execution_rehearsal_policy_version": "2.0.0"}),
            )
            with self.assertRaises(IntegrationExecutionRehearsalError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_rehearsal_fixture_root=fixture,
                    integration_execution_rehearsal_only=True,
                )
            self.assertIsNone(
                engine.store.load_artifact("production-integration-execution-rehearsal")
            )

    def test_changed_policy_manifest_and_decision_identity_fail_closed(self):
        mutators = (
            ("policy", lambda p, m: p.update({"nonsemantic_test_marker": "changed"})),
            ("manifest", lambda p, m: m.update({"nonsemantic_test_marker": "changed"})),
            (
                "decision",
                lambda p, m: m["rehearsal_decision"].update(
                    {"decision_id": "synthetic-rehearsal-decision-v2"}
                ),
            ),
        )
        for name, mutate in mutators:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_execution_preflight(td, review_ready=True)
                fixture = self.write_fixture(Path(td) / "first", engine)
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_rehearsal_fixture_root=fixture,
                    integration_execution_rehearsal_only=True,
                )
                changed = self.write_fixture(
                    Path(td) / "changed",
                    engine,
                    policy_mutator=lambda p, fn=mutate: fn(p, {}),
                    manifest_mutator=lambda m, fn=mutate: fn({}, m),
                )
                with self.assertRaises(IntegrationExecutionRehearsalError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_rehearsal_fixture_root=changed,
                        integration_execution_rehearsal_only=True,
                    )

    def test_any_real_executable_step_fails_before_final_lock(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            def make_real(m):
                m["evidence"]["noop_policy"]["steps"][3]["real_executable"] = True
            fixture = self.write_fixture(Path(td) / "unsafe", engine, manifest_mutator=make_real)
            with self.assertRaises(IntegrationExecutionRehearsalError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_rehearsal_fixture_root=fixture,
                    integration_execution_rehearsal_only=True,
                )
            self.assertIsNone(
                engine.store.load_artifact("production-integration-execution-rehearsal")
            )

    def test_paid_dependency_requirement_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            def paid(m):
                m["evidence"]["zero_incremental_cost"][
                    "other_incremental_paid_dependency_required"
                ] = True
            fixture = self.write_fixture(Path(td) / "paid", engine, manifest_mutator=paid)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-rehearsal"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertIn(
                "REHEARSAL_ZERO_INCREMENTAL_COST_GUARD_FAILED",
                data["classification_reason_codes"],
            )
            self.assertEqual(data["rehearsal_receipt_count"], 0)

    def test_real_service_receipt_substitution_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            fixture = self.write_fixture(Path(td) / "receipt-tamper", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            final = RunEngine(td, self.DATE)
            path = sorted(final.store.run_dir.glob("iteration15-rehearsal-receipt-*.json"))[0]
            receipt = final.store.read_json(path)
            receipt["external_execution_performed"] = True
            final.store._atomic_write(path, receipt)
            with self.assertRaises(IntegrationExecutionRehearsalError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_rehearsal_fixture_root=fixture,
                    integration_execution_rehearsal_only=True,
                )

    def test_evaluation_failure_recovery_reuses_locked_iterations_1_14(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_execution_preflight(td, review_ready=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-eval", engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete", "synthetic_rehearsal_evaluation_failure",
                    "execution_rehearsal:evaluation"
                ),
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            with self.assertRaises(IntegrationExecutionRehearsalBoundaryFailure):
                failing.run()
            self.assertIsNone(
                failing.store.load_artifact("production-integration-execution-rehearsal")
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(
                fresh.store.run_dir / "iteration15-execution-rehearsal-state.json"
            )
            incident = fresh.store.read_json(
                fresh.store.run_dir / "iteration15-execution-rehearsal-incident.json"
            )
            self.assertEqual(state["attempts"]["evaluation"], 2)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_one_receipt_failure_recovery_reuses_prior_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_execution_preflight(td, review_ready=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-receipt", engine)
            plan = engine.store.load_artifact("production-integration-plan")["data"]
            target = plan["plan_steps"][4]["step_id"]
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete", "synthetic_rehearsal_receipt_failure",
                    f"execution_rehearsal:receipt:{target}"
                ),
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            with self.assertRaises(IntegrationExecutionRehearsalBoundaryFailure):
                failing.run()
            self.assertEqual(
                len(list(failing.store.run_dir.glob("iteration15-rehearsal-receipt-*.json"))),
                4,
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            data = fresh.store.load_artifact(
                "production-integration-execution-rehearsal"
            )["data"]
            state = fresh.store.read_json(
                fresh.store.run_dir / "iteration15-execution-rehearsal-state.json"
            )
            self.assertEqual(data["rehearsal_receipt_count"], 10)
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 4)
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_final_artifact_failure_reuses_all_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_execution_preflight(td, review_ready=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-final", engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete", "synthetic_final_rehearsal_artifact_failure",
                    "execution_rehearsal:final_rehearsal_artifact"
                ),
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            with self.assertRaises(IntegrationExecutionRehearsalBoundaryFailure):
                failing.run()
            self.assertEqual(
                len(list(failing.store.run_dir.glob("iteration15-rehearsal-receipt-*.json"))),
                10,
            )
            self.assertIsNone(
                failing.store.load_artifact("production-integration-execution-rehearsal")
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(
                fresh.store.run_dir / "iteration15-execution-rehearsal-state.json"
            )
            incident = fresh.store.read_json(
                fresh.store.run_dir / "iteration15-execution-rehearsal-incident.json"
            )
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 10)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_fresh_engine_resume_requires_no_chat_state(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_execution_preflight(td, review_ready=True)
            fixture = self.write_fixture(Path(td) / "fresh", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            fresh = RunEngine(
                td,
                self.DATE,
                integration_execution_rehearsal_fixture_root=fixture,
                integration_execution_rehearsal_only=True,
            )
            run = fresh.run()
            data = fresh.store.load_artifact(
                "production-integration-execution-rehearsal"
            )["data"]
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(data["classification"], "rehearsal_complete")
            self.assertEqual(data["rehearsal_receipt_count"], 10)

    def test_rehearsal_only_requires_complete_locked_and_is_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE, state_root=td, integration_execution_rehearsal_only=True
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_preflight_only=True,
                    integration_execution_rehearsal_only=True,
                )

    def test_production_mode_rehearsal_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_rehearsal_only=True,
                )

    def test_rehearsal_schema_locks_safety_flags_false(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-rehearsal.schema.json"
            ).read_text()
        )
        props = schema["properties"]
        self.assertEqual(props["real_integration_steps_enabled"]["const"], 0)
        self.assertEqual(props["real_integration_steps_executed"]["const"], 0)
        self.assertTrue(props["synthetic_only"]["const"])
        self.assertFalse(props["production_action_authorized"]["const"])
        self.assertFalse(props["production_cutover_authorized"]["const"])
        self.assertFalse(props["legacy_decommission_authorized"]["const"])
        self.assertFalse(props["production_publication"]["const"])

    def test_three_consecutive_shadow_rehearsal_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                before_counts, engine = self.make_execution_preflight(
                    td, edition_date, mode="shadow"
                )
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_rehearsal_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow")
                data = final.store.load_artifact(
                    "production-integration-execution-rehearsal"
                )["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(
                    data["classification_reason_codes"][0],
                    "ITERATION14_EXECUTION_PREFLIGHT_BLOCKED",
                )
                self.assertEqual(data["rehearsal_receipt_count"], 0)
                self.assertEqual(self.locked_digests(final), before_digests)
                for stage, count in before_counts.items():
                    self.assertEqual(run["stage_executions"].get(stage), count)
                self.assert_safety_flags_false(data)
                observed.append(
                    (
                        data["classification"],
                        tuple(data["classification_reason_codes"]),
                        data["real_integration_steps_enabled"],
                        data["real_integration_steps_executed"],
                    )
                )
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(observed[1], observed[2])

    def test_three_review_ready_rehearsals_are_deterministic_by_inputs(self):
        observed = []
        for edition_date in ("2026-09-25", "2026-09-26", "2026-09-27"):
            with tempfile.TemporaryDirectory() as td:
                _, engine = self.make_execution_preflight(
                    td, edition_date, mode="shadow", review_ready=True
                )
                fixture = self.write_fixture(Path(td) / "ready", engine)
                start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_rehearsal_fixture_root=fixture,
                    integration_execution_rehearsal_only=True,
                )
                data = RunEngine(td, edition_date, mode="shadow").store.load_artifact(
                    "production-integration-execution-rehearsal"
                )["data"]
                self.assertEqual(data["classification"], "rehearsal_complete")
                self.assertEqual(data["rehearsal_receipt_count"], 10)
                self.assert_safety_flags_false(data)
                observed.append(
                    (
                        data["classification"],
                        tuple(data["classification_reason_codes"]),
                        tuple(x["step_id"] for x in data["rehearsal_receipts"]),
                    )
                )
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(observed[1], observed[2])


if __name__ == "__main__":
    unittest.main()
