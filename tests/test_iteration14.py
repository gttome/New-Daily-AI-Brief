from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_preflight import (
    IntegrationExecutionPreflightBoundaryFailure,
    IntegrationExecutionPreflightError,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration13


class Iteration14IntegrationExecutionPreflightTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration13.Iteration13IntegrationAdmissionTest(
            methodName="test_current_blocked_plan_cannot_silently_become_authorization_ready"
        )

    def fixture(self, name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration14" / name

    def make_admission(
        self,
        root: str,
        edition_date: str = DATE,
        mode: str = "synthetic",
        *,
        authorization_ready: bool = False,
    ):
        h = self.helper()
        h.make_plan(root, edition_date, mode, planned=authorization_ready)
        kwargs = {}
        if authorization_ready:
            kwargs["integration_admission_fixture_root"] = h.fixture(
                "synthetic-authorization-ready"
            )
        run = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            integration_admission_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, edition_date, mode=mode)

    def locked_digests(self, engine: RunEngine):
        values = self.helper().locked_digests(engine)
        values["production-integration-admission"] = engine.store.load_artifact(
            "production-integration-admission"
        )["content_digest"]
        return values

    def write_fixture(
        self,
        root: Path,
        engine: RunEngine,
        *,
        source: str = "synthetic-execution-review-ready",
        policy_mutator=None,
        manifest_mutator=None,
    ) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        policy = json.loads(
            (self.fixture(source) / "execution-preflight-policy.json").read_text()
        )
        manifest = json.loads(
            (self.fixture(source) / "execution-envelope-manifest.json").read_text()
        )
        plan = engine.store.load_artifact("production-integration-plan")
        if plan and manifest["evidence"]["step_selection_scope"] is not None:
            plan_data = plan["data"]
            manifest["evidence"]["step_selection_scope"]["plan_id"] = plan_data["plan_id"]
            manifest["evidence"]["step_selection_scope"]["plan_graph_digest"] = digest(
                plan_data["plan_steps"]
            )
            manifest["evidence"]["step_enablement"]["plan_id"] = plan_data["plan_id"]
            manifest["evidence"]["dry_run_assertions"][
                "dry_run_assertion_set_digest"
            ] = digest(plan_data["dry_run_assertion_set"])
            manifest["evidence"]["rollback_restore"][
                "rollback_boundary_set_digest"
            ] = digest(plan_data["rollback_boundary_set"])
        if policy_mutator:
            policy_mutator(policy)
        if manifest_mutator:
            manifest_mutator(manifest)
        (root / "execution-preflight-policy.json").write_text(json.dumps(policy))
        (root / "execution-envelope-manifest.json").write_text(json.dumps(manifest))
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

    def test_current_blocked_admission_cannot_silently_become_execution_review_ready(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_admission(td)
            before_digests = self.locked_digests(engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_only=True,
            )
            final = RunEngine(td, self.DATE)
            artifact = final.store.load_artifact(
                "production-integration-execution-preflight"
            )
            data = artifact["data"]
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(run["completion_status"], "complete_locked")
            self.assertEqual(data["admission_classification"], "blocked")
            self.assertEqual(data["classification"], "blocked")
            self.assertNotEqual(data["classification"], "execution_review_ready")
            self.assertEqual(
                data["classification_reason_codes"][0],
                "ITERATION13_ADMISSION_BLOCKED",
            )
            self.assertEqual(
                len(
                    list(
                        final.store.run_dir.glob(
                            "production-integration-execution-preflight.json"
                        )
                    )
                ),
                1,
            )
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)
            self.assert_safety_flags_false(data)

    def test_authorization_ready_admission_alone_is_insufficient_without_execution_envelope(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_admission(td, authorization_ready=True)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-preflight"
            )["data"]
            self.assertEqual(data["admission_classification"], "authorization_ready")
            self.assertEqual(data["classification"], "blocked")
            self.assertIn(
                "EXECUTION_EXECUTOR_CONTRACT_MISSING",
                data["classification_reason_codes"],
            )
            self.assertIn(
                "EXECUTION_ENVELOPE_DECISION_MISSING",
                data["classification_reason_codes"],
            )
            self.assertFalse(data["production_action_authorized"])

    def test_complete_synthetic_execution_envelope_is_logically_execution_review_ready_only(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)
            fixture = self.write_fixture(Path(td) / "ready-envelope", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-preflight"
            )["data"]
            self.assertEqual(data["admission_classification"], "authorization_ready")
            self.assertEqual(data["classification"], "execution_review_ready")
            self.assertEqual(
                data["classification_reason_codes"],
                ["EXECUTION_ENVELOPE_COMPLETE_SYNTHETIC_ONLY"],
            )
            self.assertEqual(
                data["execution_envelope_decision_id"],
                "synthetic-execution-envelope-decision-v1",
            )
            self.assertTrue(data["synthetic_only"])
            self.assertEqual(data["real_integration_steps_enabled"], 0)
            self.assertEqual(len(data["execution_steps"]), 10)
            self.assertTrue(all(step["enabled"] is False for step in data["execution_steps"]))
            self.assert_safety_flags_false(data)

    def test_complete_envelope_without_separate_execution_decision_remains_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)
            fixture = self.write_fixture(
                Path(td) / "no-decision",
                engine,
                manifest_mutator=lambda m: m.__setitem__(
                    "execution_envelope_decision", None
                ),
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-preflight"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertEqual(
                data["classification_reason_codes"],
                ["EXECUTION_ENVELOPE_DECISION_MISSING"],
            )
            self.assertIsNone(data["execution_envelope_decision_id"])

    def test_execution_preflight_binds_exact_admission_plan_and_transitive_upstream_identities(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)
            fixture = self.write_fixture(Path(td) / "binding", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            final = RunEngine(td, self.DATE)
            artifact = final.store.load_artifact(
                "production-integration-execution-preflight"
            )
            admission = final.store.load_artifact("production-integration-admission")
            plan = final.store.load_artifact("production-integration-plan")
            preflight = final.store.load_artifact("production-integration-preflight")
            readiness = final.store.load_artifact("readiness-admission")
            completion = final.store.load_artifact("completion")
            data = artifact["data"]
            self.assertEqual(artifact["input_digests"], [admission["content_digest"]])
            self.assertEqual(data["admission_artifact_digest"], admission["content_digest"])
            self.assertEqual(data["admission_id"], admission["data"]["admission_id"])
            self.assertEqual(data["plan_artifact_digest"], plan["content_digest"])
            self.assertEqual(data["plan_id"], plan["data"]["plan_id"])
            self.assertEqual(data["plan_graph_digest"], digest(plan["data"]["plan_steps"]))
            self.assertEqual(
                data["dry_run_assertion_set_digest"],
                digest(plan["data"]["dry_run_assertion_set"]),
            )
            self.assertEqual(
                data["rollback_boundary_set_digest"],
                digest(plan["data"]["rollback_boundary_set"]),
            )
            self.assertEqual(data["preflight_artifact_digest"], preflight["content_digest"])
            self.assertEqual(data["preflight_id"], preflight["data"]["preflight_id"])
            self.assertEqual(data["readiness_artifact_digest"], readiness["content_digest"])
            self.assertEqual(data["readiness_assessment_id"], readiness["data"]["assessment_id"])
            self.assertEqual(data["completion_artifact_digest"], completion["content_digest"])
            self.assertEqual(
                data["canonical_chain_digest"],
                completion["data"]["canonical_chain_digest"],
            )

    def test_execution_preflight_identity_is_deterministic_and_replay_reuses_one_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)
            fixture = self.write_fixture(Path(td) / "replay", engine)
            kwargs = {
                "integration_execution_preflight_fixture_root": fixture,
                "integration_execution_preflight_only": True,
            }
            first = start_daily_brief(self.DATE, state_root=td, **kwargs)
            artifact1 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-preflight"
            )
            counts = deepcopy(first["stage_executions"])
            second = start_daily_brief(self.DATE, state_root=td, **kwargs)
            final = RunEngine(td, self.DATE)
            artifact2 = final.store.load_artifact(
                "production-integration-execution-preflight"
            )
            self.assertEqual(artifact2["content_digest"], artifact1["content_digest"])
            self.assertEqual(
                artifact2["data"]["execution_preflight_id"],
                artifact1["data"]["execution_preflight_id"],
            )
            self.assertEqual(second["stage_executions"], counts)
            self.assertEqual(
                len(
                    list(
                        final.store.run_dir.glob(
                            "production-integration-execution-preflight.json"
                        )
                    )
                ),
                1,
            )

    def test_execution_preflight_does_not_reexecute_or_rebuild_locked_iterations1_13(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_admission(td, authorization_ready=True)
            before_digests = self.locked_digests(engine)
            admission_state_path = engine.store.run_dir / "iteration13-admission-state.json"
            admission_state_before = engine.store.read_json(admission_state_path)
            fixture = self.write_fixture(Path(td) / "anti-rework", engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            final = RunEngine(td, self.DATE)
            admission_state_after = final.store.read_json(admission_state_path)
            self.assertEqual(
                admission_state_after["attempts"]["admission_evaluation"],
                admission_state_before["attempts"]["admission_evaluation"],
            )
            self.assertEqual(
                admission_state_after["attempts"]["artifact_assembly"],
                admission_state_before["attempts"]["artifact_assembly"],
            )
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)
            metrics = final.store.read_json(
                final.store.run_dir / "iteration14-execution-preflight-metrics.json"
            )
            self.assertEqual(
                metrics["anti_rework"]["locked_iterations_1_13_reexecution"], 0
            )
            self.assertEqual(
                metrics["anti_rework"]["iteration13_admission_evaluation_reexecution"],
                0,
            )
            self.assertEqual(
                metrics["anti_rework"]["iteration13_admission_artifact_rebuild"], 0
            )
            self.assertEqual(metrics["anti_rework"]["full_pipeline_restarts"], 0)

    def test_corrupted_or_stale_iteration13_admission_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_admission(td, authorization_ready=True)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-admission")
            artifact = engine.store.read_json(path)
            artifact["data"]["classification"] = "blocked"
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationExecutionPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_only=True,
                )

        with tempfile.TemporaryDirectory() as td:
            self.make_admission(td, authorization_ready=True)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-admission")
            artifact = engine.store.read_json(path)
            artifact["data"]["completion_scope"] = "stale_scope"
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationExecutionPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_only=True,
                )

    def test_unsupported_execution_preflight_policy_or_schema_version_fails_closed(self):
        for field in ("execution_preflight_policy_version", "schema_version"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_admission(td, authorization_ready=True)
                fixture = self.write_fixture(
                    Path(td) / f"bad-{field}",
                    engine,
                    policy_mutator=lambda p, field=field: p.__setitem__(field, "9.9.9"),
                )
                with self.assertRaises(IntegrationExecutionPreflightError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_preflight_fixture_root=fixture,
                        integration_execution_preflight_only=True,
                    )

    def test_changed_admission_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_admission(td, authorization_ready=True)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-admission")
            artifact = engine.store.read_json(path)
            artifact["data"]["admission_id"] = "sha256:changed-admission-identity"
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationExecutionPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_only=True,
                )

    def test_changed_execution_policy_identity_fails_closed_instead_of_reusing_cache(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)
            ready = self.write_fixture(Path(td) / "ready", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=ready,
                integration_execution_preflight_only=True,
            )
            changed = self.write_fixture(
                Path(td) / "changed-policy",
                engine,
                policy_mutator=lambda p: p.__setitem__("policy_note", "identity-changed"),
            )
            with self.assertRaises(IntegrationExecutionPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_fixture_root=changed,
                    integration_execution_preflight_only=True,
                )

    def test_changed_execution_manifest_identity_fails_closed_instead_of_reusing_cache(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)
            ready = self.write_fixture(Path(td) / "ready", engine)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=ready,
                integration_execution_preflight_only=True,
            )
            changed = self.write_fixture(
                Path(td) / "changed-manifest",
                engine,
                manifest_mutator=lambda m: m.__setitem__(
                    "manifest_note", "identity-changed"
                ),
            )
            with self.assertRaises(IntegrationExecutionPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_fixture_root=changed,
                    integration_execution_preflight_only=True,
                )

    def test_missing_required_execution_envelope_inputs_remain_blocked(self):
        reasons = {
            "executor_contract": "EXECUTION_EXECUTOR_CONTRACT_MISSING",
            "step_selection_scope": "EXECUTION_STEP_SELECTION_SCOPE_MISSING",
            "step_enablement": "EXECUTION_STEP_ENABLEMENT_MISSING",
            "dry_run_assertions": "EXECUTION_DRY_RUN_BINDING_MISSING",
            "rollback_restore": "EXECUTION_ROLLBACK_RESTORE_BINDING_MISSING",
            "target_environment": "EXECUTION_TARGET_ENVIRONMENT_MISSING",
            "pre_execution_verification": "EXECUTION_PRE_EXECUTION_VERIFICATION_MISSING",
            "stop_abort_conditions": "EXECUTION_STOP_ABORT_CONDITIONS_MISSING",
            "cutover_decommission_state": "EXECUTION_CUTOVER_DECOMMISSION_STATE_MISSING",
            "zero_incremental_cost": "EXECUTION_ZERO_INCREMENTAL_COST_GUARD_MISSING",
        }
        for key, reason in reasons.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_admission(td, authorization_ready=True)
                fixture = self.write_fixture(
                    Path(td) / f"missing-{key}",
                    engine,
                    manifest_mutator=lambda m, key=key: m["evidence"].__setitem__(
                        key, None
                    ),
                )
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_fixture_root=fixture,
                    integration_execution_preflight_only=True,
                )
                data = RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-preflight"
                )["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertIn(reason, data["classification_reason_codes"])

    def test_paid_dependency_without_zero_incremental_cost_guard_remains_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)

            def mutate(manifest):
                record = manifest["evidence"]["zero_incremental_cost"]
                record["zero_incremental_cost"] = False
                record["paid_deployment_or_hosting_api_required"] = True

            fixture = self.write_fixture(
                Path(td) / "paid-dependency",
                engine,
                manifest_mutator=mutate,
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-preflight"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertIn(
                "EXECUTION_ZERO_INCREMENTAL_COST_GUARD_FAILED",
                data["classification_reason_codes"],
            )

    def test_any_enabled_real_integration_step_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)

            def mutate(manifest):
                manifest["evidence"]["step_enablement"]["steps"][0]["enabled"] = True

            fixture = self.write_fixture(
                Path(td) / "enabled-step",
                engine,
                manifest_mutator=mutate,
            )
            with self.assertRaises(IntegrationExecutionPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_fixture_root=fixture,
                    integration_execution_preflight_only=True,
                )
            self.assertIsNone(
                RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-preflight"
                )
            )

    def test_incomplete_iteration13_operational_closure_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_admission(td, authorization_ready=True)
            fixture = self.write_fixture(
                Path(td) / "closure-pending",
                engine,
                manifest_mutator=lambda m: m["iteration13_closure"].__setitem__(
                    "repository_closure_status", "pending"
                ),
            )
            with self.assertRaises(IntegrationExecutionPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_fixture_root=fixture,
                    integration_execution_preflight_only=True,
                )

    def test_execution_preflight_evaluation_failure_recovers_on_fresh_engine_without_upstream_rework(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_admission(td, authorization_ready=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-eval", engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_execution_preflight_evaluation_failure",
                    "execution_preflight:evaluation",
                ),
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            with self.assertRaises(IntegrationExecutionPreflightBoundaryFailure):
                failing.run()
            self.assertIsNone(
                failing.store.load_artifact(
                    "production-integration-execution-preflight"
                )
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(
                fresh.store.run_dir / "iteration14-execution-preflight-state.json"
            )
            incident = fresh.store.read_json(
                fresh.store.run_dir / "iteration14-execution-preflight-incident.json"
            )
            self.assertEqual(state["attempts"]["execution_preflight_evaluation"], 2)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "evaluation")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_final_execution_preflight_artifact_failure_reuses_durable_evaluation(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_admission(td, authorization_ready=True)
            before_digests = self.locked_digests(engine)
            fixture = self.write_fixture(Path(td) / "recover-artifact", engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_final_execution_preflight_artifact_failure",
                    "execution_preflight:final_execution_preflight_artifact",
                ),
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            with self.assertRaises(IntegrationExecutionPreflightBoundaryFailure):
                failing.run()
            state_after_failure = failing.store.read_json(
                failing.store.run_dir / "iteration14-execution-preflight-state.json"
            )
            self.assertIsNotNone(state_after_failure["evaluation"])
            self.assertIsNone(
                failing.store.load_artifact(
                    "production-integration-execution-preflight"
                )
            )
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_preflight_fixture_root=fixture,
                integration_execution_preflight_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(
                fresh.store.run_dir / "iteration14-execution-preflight-state.json"
            )
            incident = fresh.store.read_json(
                fresh.store.run_dir / "iteration14-execution-preflight-incident.json"
            )
            self.assertEqual(state["attempts"]["execution_preflight_evaluation"], 1)
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(
                state["metrics"]["execution_preflight_evaluation_reuse"], 1
            )
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(
                incident["recovery_receipt"]["boundary_id"],
                "final_execution_preflight_artifact",
            )
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_execution_preflight_contract_schema_is_versioned_and_non_authorizing(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-preflight.schema.json"
            ).read_text()
        )
        self.assertEqual(
            schema["properties"]["execution_preflight_schema_version"]["const"],
            "1.0.0",
        )
        self.assertEqual(
            schema["properties"]["execution_preflight_policy_version"]["const"],
            "1.0.0",
        )
        self.assertEqual(
            schema["properties"]["classification"]["enum"],
            ["blocked", "execution_review_ready", "invalid"],
        )
        self.assertEqual(
            schema["properties"]["real_integration_steps_enabled"]["const"], 0
        )
        self.assertFalse(schema["properties"]["production_action_authorized"]["const"])
        self.assertFalse(
            schema["properties"]["production_cutover_authorized"]["const"]
        )
        self.assertFalse(
            schema["properties"]["legacy_decommission_authorized"]["const"]
        )
        self.assertFalse(schema["properties"]["production_publication"]["const"])

    def test_execution_preflight_only_requires_complete_locked_and_is_exclusive(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_preflight_only=True,
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_admission_only=True,
                    integration_execution_preflight_only=True,
                )

    def test_three_consecutive_shadow_execution_preflight_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                before_counts, engine = self.make_admission(
                    td, edition_date, mode="shadow"
                )
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_preflight_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow")
                artifact = final.store.load_artifact(
                    "production-integration-execution-preflight"
                )
                data = artifact["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(
                    data["classification_reason_codes"][0],
                    "ITERATION13_ADMISSION_BLOCKED",
                )
                self.assertEqual(data["real_integration_steps_enabled"], 0)
                self.assertEqual(
                    len(
                        list(
                            final.store.run_dir.glob(
                                "production-integration-execution-preflight.json"
                            )
                        )
                    ),
                    1,
                )
                self.assertEqual(self.locked_digests(final), before_digests)
                for stage, count in before_counts.items():
                    self.assertEqual(run["stage_executions"].get(stage), count)
                self.assert_safety_flags_false(data)
                observed.append(
                    (
                        data["classification"],
                        tuple(data["classification_reason_codes"]),
                    )
                )
        self.assertEqual(len(observed), 3)
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(observed[1], observed[2])


if __name__ == "__main__":
    unittest.main()
