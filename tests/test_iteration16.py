from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_authorization_review import (
    IntegrationExecutionAuthorizationReviewBoundaryFailure,
    IntegrationExecutionAuthorizationReviewError,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration15


class Iteration16ExecutionAuthorizationReviewTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration15.Iteration15IntegrationExecutionRehearsalTest(
            methodName="test_current_blocked_execution_preflight_remains_blocked"
        )

    def fixture(self, name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration16" / name

    def make_rehearsal(
        self,
        root: str,
        edition_date: str = DATE,
        mode: str = "synthetic",
        *,
        rehearsal_complete: bool = False,
    ):
        h = self.helper()
        _, engine = h.make_execution_preflight(
            root, edition_date, mode, review_ready=rehearsal_complete
        )
        kwargs = {}
        if rehearsal_complete:
            fixture = h.write_fixture(Path(root) / "iteration15-ready", engine)
            kwargs["integration_execution_rehearsal_fixture_root"] = fixture
        run = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            integration_execution_rehearsal_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, edition_date, mode=mode)

    def locked_digests(self, engine: RunEngine):
        values = self.helper().locked_digests(engine)
        values["production-integration-execution-rehearsal"] = engine.store.load_artifact(
            "production-integration-execution-rehearsal"
        )["content_digest"]
        return values

    def write_fixture(
        self,
        root: Path,
        engine: RunEngine,
        *,
        source: str = "synthetic-authorization-review-ready",
        policy_mutator=None,
        manifest_mutator=None,
    ) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        policy = json.loads(
            (self.fixture(source) / "authorization-review-policy.json").read_text()
        )
        manifest = json.loads(
            (self.fixture(source) / "authorization-review-manifest.json").read_text()
        )
        rehearsal = engine.store.load_artifact(
            "production-integration-execution-rehearsal"
        )
        plan = engine.store.load_artifact("production-integration-plan")
        rd = rehearsal["data"]
        pd = plan["data"]
        receipts = rd["rehearsal_receipts"]
        evidence = manifest["evidence"]
        evidence["rehearsal_identity"].update(
            {
                "execution_rehearsal_artifact_digest": rehearsal["content_digest"],
                "execution_rehearsal_id": rd["execution_rehearsal_id"],
                "execution_attempt_id": rd["execution_attempt_id"],
                "rehearsal_policy_id": rd["execution_rehearsal_policy_id"],
                "rehearsal_policy_digest": rd["execution_rehearsal_policy_digest"],
                "rehearsal_manifest_id": rd["rehearsal_envelope_manifest_id"],
                "rehearsal_manifest_digest": rd["rehearsal_envelope_manifest_digest"],
                "rehearsal_decision_id": rd["rehearsal_decision_id"],
                "rehearsal_decision_digest": rd["rehearsal_decision_digest"],
            }
        )
        evidence["receipt_inventory"]["receipt_ids"] = [
            item["receipt_id"] for item in receipts
        ]
        evidence["receipt_inventory"]["receipt_set_digest"] = digest(receipts)
        evidence["receipt_verification"]["receipt_set_digest"] = digest(receipts)
        evidence["step_selection_scope"]["plan_id"] = pd["plan_id"]
        evidence["step_selection_scope"]["plan_graph_digest"] = digest(
            pd["plan_steps"]
        )
        evidence["step_selection_scope"]["step_ids"] = [
            item["step_id"] for item in pd["plan_steps"]
        ]
        evidence["rollback_recovery_policy"][
            "rollback_boundary_set_digest"
        ] = digest(pd["rollback_boundary_set"])
        manifest["authorization_review_decision"][
            "execution_rehearsal_id"
        ] = rd["execution_rehearsal_id"]
        if policy_mutator:
            policy_mutator(policy)
        if manifest_mutator:
            manifest_mutator(manifest)
        (root / "authorization-review-policy.json").write_text(json.dumps(policy))
        (root / "authorization-review-manifest.json").write_text(json.dumps(manifest))
        return root

    def assert_safety_flags_false(self, data):
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_executor_invocation_authorized",
            "credentials_use_authorized",
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
        self.assertTrue(all(item["enabled"] is False for item in data["execution_steps"]))

    def test_current_blocked_rehearsal_remains_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_rehearsal(td)
            before_digests = self.locked_digests(engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_only=True,
            )
            final = RunEngine(td, self.DATE)
            data = final.store.load_artifact(
                "production-integration-execution-authorization-review"
            )["data"]
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(run["completion_status"], "complete_locked")
            self.assertEqual(data["rehearsal_classification"], "blocked")
            self.assertEqual(data["classification"], "blocked")
            self.assertEqual(
                data["classification_reason_codes"][0],
                "ITERATION15_EXECUTION_REHEARSAL_BLOCKED",
            )
            self.assertEqual(data["receipt_verification_count"], 0)
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)
            self.assert_safety_flags_false(data)

    def test_rehearsal_complete_alone_is_insufficient(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_rehearsal(td, rehearsal_complete=True)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-authorization-review"
            )["data"]
            self.assertEqual(data["rehearsal_classification"], "rehearsal_complete")
            self.assertEqual(data["classification"], "blocked")
            self.assertIn(
                "AUTH_REVIEW_REHEARSAL_IDENTITY_MISSING",
                data["classification_reason_codes"],
            )
            self.assertIn(
                "AUTH_REVIEW_DECISION_MISSING", data["classification_reason_codes"]
            )
            self.assertEqual(data["receipt_verification_count"], 0)

    def test_separate_review_decision_is_required(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)
            fixture = self.write_fixture(
                Path(td) / "no-decision",
                engine,
                manifest_mutator=lambda manifest: manifest.update(
                    {"authorization_review_decision": None}
                ),
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-authorization-review"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertIn(
                "AUTH_REVIEW_DECISION_MISSING", data["classification_reason_codes"]
            )
            self.assertEqual(data["receipt_verification_count"], 0)

    def test_fully_qualified_synthetic_review_is_review_ready_only(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_rehearsal(td, rehearsal_complete=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "ready", engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            final = RunEngine(td, self.DATE)
            data = final.store.load_artifact(
                "production-integration-execution-authorization-review"
            )["data"]
            self.assertEqual(data["classification"], "authorization_review_ready")
            self.assertEqual(
                data["classification_reason_codes"],
                ["SYNTHETIC_AUTHORIZATION_REVIEW_READY"],
            )
            self.assertEqual(
                data["authorization_review_decision_id"],
                "synthetic-authorization-review-decision-v1",
            )
            self.assertEqual(data["receipt_verification_count"], 10)
            self.assertEqual(len(data["receipt_verifications"]), 10)
            self.assertEqual(
                [item["position"] for item in data["receipt_verifications"]],
                list(range(1, 11)),
            )
            self.assertTrue(
                all(item["noop_verified"] for item in data["receipt_verifications"])
            )
            self.assertTrue(
                all(
                    item["side_effect_free_verified"]
                    for item in data["receipt_verifications"]
                )
            )
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)
            self.assert_safety_flags_false(data)

    def test_exact_iteration15_and_transitive_bindings_are_preserved(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)
            fixture = self.write_fixture(Path(td) / "bindings", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            final = RunEngine(td, self.DATE)
            data = final.store.load_artifact(
                "production-integration-execution-authorization-review"
            )["data"]
            rehearsal = final.store.load_artifact(
                "production-integration-execution-rehearsal"
            )
            ep = final.store.load_artifact(
                "production-integration-execution-preflight"
            )
            admission = final.store.load_artifact("production-integration-admission")
            plan = final.store.load_artifact("production-integration-plan")
            preflight = final.store.load_artifact("production-integration-preflight")
            readiness = final.store.load_artifact("readiness-admission")
            completion = final.store.load_artifact("completion")
            self.assertEqual(
                data["execution_rehearsal_artifact_digest"],
                rehearsal["content_digest"],
            )
            self.assertEqual(
                data["execution_rehearsal_id"],
                rehearsal["data"]["execution_rehearsal_id"],
            )
            self.assertEqual(
                data["execution_attempt_id"],
                rehearsal["data"]["execution_attempt_id"],
            )
            self.assertEqual(
                data["execution_preflight_artifact_digest"], ep["content_digest"]
            )
            self.assertEqual(
                data["admission_artifact_digest"], admission["content_digest"]
            )
            self.assertEqual(data["plan_artifact_digest"], plan["content_digest"])
            self.assertEqual(data["plan_graph_digest"], digest(plan["data"]["plan_steps"]))
            self.assertEqual(
                data["dry_run_assertion_set_digest"],
                digest(plan["data"]["dry_run_assertion_set"]),
            )
            self.assertEqual(
                data["rollback_boundary_set_digest"],
                digest(plan["data"]["rollback_boundary_set"]),
            )
            self.assertEqual(
                data["preflight_artifact_digest"], preflight["content_digest"]
            )
            self.assertEqual(
                data["readiness_artifact_digest"], readiness["content_digest"]
            )
            self.assertEqual(
                data["completion_artifact_digest"], completion["content_digest"]
            )

    def test_deterministic_replay_reuses_final_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)
            fixture = self.write_fixture(Path(td) / "replay", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            first = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-authorization-review"
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            second = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-authorization-review"
            )
            self.assertEqual(first["content_digest"], second["content_digest"])
            self.assertEqual(
                first["data"]["authorization_review_id"],
                second["data"]["authorization_review_id"],
            )

    def test_corrupted_iteration15_input_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)
            artifact = engine.store.load_artifact(
                "production-integration-execution-rehearsal"
            )
            artifact["data"]["classification_reason_codes"] = ["tampered"]
            engine.store._atomic_write(
                engine.store.artifact_path(
                    "production-integration-execution-rehearsal"
                ),
                artifact,
            )
            with self.assertRaises(IntegrationExecutionAuthorizationReviewError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_authorization_review_only=True,
                )

    def test_reordered_or_duplicated_receipts_fail_closed(self):
        for kind in ("reordered", "duplicated"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_rehearsal(td, rehearsal_complete=True)
                artifact = engine.store.load_artifact(
                    "production-integration-execution-rehearsal"
                )
                receipts = artifact["data"]["rehearsal_receipts"]
                if kind == "reordered":
                    receipts[0], receipts[1] = receipts[1], receipts[0]
                else:
                    receipts[1] = deepcopy(receipts[0])
                artifact["content_digest"] = semantic_digest(artifact)
                engine.store._atomic_write(
                    engine.store.artifact_path(
                        "production-integration-execution-rehearsal"
                    ),
                    artifact,
                )
                with self.assertRaises(
                    IntegrationExecutionAuthorizationReviewError
                ):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_authorization_review_only=True,
                    )

    def test_corrupted_or_real_service_receipt_substitution_fails_closed(self):
        for mutation in ("corrupt", "real-service"):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_rehearsal(td, rehearsal_complete=True)
                path = sorted(
                    engine.store.run_dir.glob("iteration15-rehearsal-receipt-*.json")
                )[0]
                receipt = engine.store.read_json(path)
                if mutation == "corrupt":
                    receipt["receipt_id"] = "sha256:corrupted"
                else:
                    receipt["real_service_contacted"] = True
                engine.store._atomic_write(path, receipt)
                with self.assertRaises(
                    IntegrationExecutionAuthorizationReviewError
                ):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_authorization_review_only=True,
                    )

    def test_unsupported_review_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)
            fixture = self.write_fixture(
                Path(td) / "unsupported",
                engine,
                policy_mutator=lambda policy: policy.update(
                    {"authorization_review_policy_version": "2.0.0"}
                ),
            )
            with self.assertRaises(IntegrationExecutionAuthorizationReviewError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_authorization_review_fixture_root=fixture,
                    integration_execution_authorization_review_only=True,
                )

    def test_changed_policy_manifest_or_decision_identity_fails_closed(self):
        cases = (
            ("policy", lambda policy: policy.update({"marker": "changed"}), None),
            ("manifest", None, lambda manifest: manifest.update({"marker": "changed"})),
            (
                "decision",
                None,
                lambda manifest: manifest["authorization_review_decision"].update(
                    {"decision_id": "synthetic-authorization-review-decision-v2"}
                ),
            ),
        )
        for name, policy_mutator, manifest_mutator in cases:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_rehearsal(td, rehearsal_complete=True)
                fixture = self.write_fixture(Path(td) / "first", engine)
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_authorization_review_fixture_root=fixture,
                    integration_execution_authorization_review_only=True,
                )
                changed = self.write_fixture(
                    Path(td) / "changed",
                    engine,
                    policy_mutator=policy_mutator,
                    manifest_mutator=manifest_mutator,
                )
                with self.assertRaises(
                    IntegrationExecutionAuthorizationReviewError
                ):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_authorization_review_fixture_root=changed,
                        integration_execution_authorization_review_only=True,
                    )

    def test_any_authority_flag_fails_closed(self):
        mutations = (
            lambda manifest: manifest.update(
                {"real_executor_invocation_authorized": True}
            ),
            lambda manifest: manifest["authorization_review_decision"].update(
                {"credentials_use_authorized": True}
            ),
            lambda manifest: manifest["evidence"]["target_environment"].update(
                {"production_action_authorized": True}
            ),
        )
        for mutate in mutations:
            with self.subTest(mutation=str(mutate)), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_rehearsal(td, rehearsal_complete=True)
                fixture = self.write_fixture(
                    Path(td) / "unsafe", engine, manifest_mutator=mutate
                )
                with self.assertRaises(
                    IntegrationExecutionAuthorizationReviewError
                ):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_authorization_review_fixture_root=fixture,
                        integration_execution_authorization_review_only=True,
                    )

    def test_any_real_executable_step_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)
            artifact = engine.store.load_artifact(
                "production-integration-execution-rehearsal"
            )
            artifact["data"]["execution_steps"][0]["enabled"] = True
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(
                engine.store.artifact_path(
                    "production-integration-execution-rehearsal"
                ),
                artifact,
            )
            with self.assertRaises(IntegrationExecutionAuthorizationReviewError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_authorization_review_only=True,
                )

    def test_paid_dependency_requirement_blocks_review(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)

            def paid(manifest):
                manifest["evidence"]["zero_incremental_cost"][
                    "other_incremental_paid_dependency_required"
                ] = True

            fixture = self.write_fixture(
                Path(td) / "paid", engine, manifest_mutator=paid
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-authorization-review"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertIn(
                "AUTH_REVIEW_ZERO_INCREMENTAL_COST_GUARD_FAILED",
                data["classification_reason_codes"],
            )
            self.assertEqual(data["receipt_verification_count"], 0)

    def test_evaluation_failure_recovery_reuses_locked_iterations_1_15(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_rehearsal(td, rehearsal_complete=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-eval", engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_authorization_review_evaluation_failure",
                    "authorization_review:evaluation",
                ),
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            with self.assertRaises(
                IntegrationExecutionAuthorizationReviewBoundaryFailure
            ):
                failing.run()
            self.assertIsNone(
                failing.store.load_artifact(
                    "production-integration-execution-authorization-review"
                )
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(
                fresh.store.run_dir
                / "iteration16-execution-authorization-review-state.json"
            )
            incident = fresh.store.read_json(
                fresh.store.run_dir
                / "iteration16-execution-authorization-review-incident.json"
            )
            self.assertEqual(state["attempts"]["evaluation"], 2)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)
            self.assertEqual(
                state["metrics"]["anti_rework"]["locked_iterations_1_15_reexecution"],
                0,
            )
            self.assertEqual(
                state["metrics"]["anti_rework"]["full_pipeline_restarts"], 0
            )

    def test_receipt_verification_failure_reuses_prior_verifications(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_rehearsal(td, rehearsal_complete=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-receipt", engine)
            plan = engine.store.load_artifact("production-integration-plan")["data"]
            target = plan["plan_steps"][4]["step_id"]
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_authorization_review_receipt_failure",
                    f"authorization_review:receipt:{target}",
                ),
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            with self.assertRaises(
                IntegrationExecutionAuthorizationReviewBoundaryFailure
            ):
                failing.run()
            self.assertEqual(
                len(
                    list(
                        failing.store.run_dir.glob(
                            "iteration16-authorization-review-receipt-verification-*.json"
                        )
                    )
                ),
                4,
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(
                fresh.store.run_dir
                / "iteration16-execution-authorization-review-state.json"
            )
            self.assertGreaterEqual(
                state["metrics"]["receipt_verification_reuse"], 4
            )
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_final_artifact_failure_reuses_all_receipt_verifications(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_rehearsal(td, rehearsal_complete=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-final", engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_final_authorization_review_artifact_failure",
                    "authorization_review:final_authorization_review_artifact",
                ),
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            with self.assertRaises(
                IntegrationExecutionAuthorizationReviewBoundaryFailure
            ):
                failing.run()
            self.assertEqual(
                len(
                    list(
                        failing.store.run_dir.glob(
                            "iteration16-authorization-review-receipt-verification-*.json"
                        )
                    )
                ),
                10,
            )
            self.assertIsNone(
                failing.store.load_artifact(
                    "production-integration-execution-authorization-review"
                )
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(
                fresh.store.run_dir
                / "iteration16-execution-authorization-review-state.json"
            )
            incident = fresh.store.read_json(
                fresh.store.run_dir
                / "iteration16-execution-authorization-review-incident.json"
            )
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(
                state["metrics"]["receipt_verification_reuse"], 10
            )
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_fresh_engine_no_chat_resume(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_rehearsal(td, rehearsal_complete=True)
            fixture = self.write_fixture(Path(td) / "fresh", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            fresh = RunEngine(
                td,
                self.DATE,
                integration_execution_authorization_review_fixture_root=fixture,
                integration_execution_authorization_review_only=True,
            )
            run = fresh.run()
            data = fresh.store.load_artifact(
                "production-integration-execution-authorization-review"
            )["data"]
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(data["classification"], "authorization_review_ready")
            self.assertEqual(data["receipt_verification_count"], 10)

    def test_bounded_path_requires_complete_locked_and_is_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_authorization_review_only=True,
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_rehearsal_only=True,
                    integration_execution_authorization_review_only=True,
                )

    def test_production_mode_review_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_authorization_review_only=True,
                )

    def test_schema_locks_all_authority_flags_false(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-authorization-review.schema.json"
            ).read_text()
        )
        properties = schema["properties"]
        self.assertEqual(properties["real_integration_steps_enabled"]["const"], 0)
        self.assertEqual(properties["real_integration_steps_executed"]["const"], 0)
        self.assertTrue(properties["synthetic_only"]["const"])
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_executor_invocation_authorized",
            "credentials_use_authorized",
        ):
            self.assertFalse(properties[flag]["const"])

    def test_three_consecutive_shadow_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                before_counts, engine = self.make_rehearsal(
                    td, edition_date, mode="shadow"
                )
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_authorization_review_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow")
                data = final.store.load_artifact(
                    "production-integration-execution-authorization-review"
                )["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(
                    data["classification_reason_codes"][0],
                    "ITERATION15_EXECUTION_REHEARSAL_BLOCKED",
                )
                self.assertEqual(data["receipt_verification_count"], 0)
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

    def test_three_synthetic_review_ready_proofs_are_deterministic(self):
        observed = []
        for edition_date in ("2026-09-25", "2026-09-26", "2026-09-27"):
            with tempfile.TemporaryDirectory() as td:
                _, engine = self.make_rehearsal(
                    td, edition_date, mode="shadow", rehearsal_complete=True
                )
                fixture = self.write_fixture(Path(td) / "ready", engine)
                start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_authorization_review_fixture_root=fixture,
                    integration_execution_authorization_review_only=True,
                )
                data = RunEngine(td, edition_date, mode="shadow").store.load_artifact(
                    "production-integration-execution-authorization-review"
                )["data"]
                self.assertEqual(data["classification"], "authorization_review_ready")
                self.assertEqual(data["receipt_verification_count"], 10)
                self.assert_safety_flags_false(data)
                observed.append(
                    (
                        data["classification"],
                        tuple(data["classification_reason_codes"]),
                        tuple(
                            item["step_id"]
                            for item in data["receipt_verifications"]
                        ),
                    )
                )
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(observed[1], observed[2])


if __name__ == "__main__":
    unittest.main()
