from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_admission import (
    IntegrationAdmissionBoundaryFailure,
    IntegrationAdmissionError,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration12


class Iteration13IntegrationAdmissionTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration12.Iteration12IntegrationPlanTest(
            methodName="test_current_unresolved_preflight_is_dedicatedly_blocked_and_never_planned"
        )

    def fixture(self, name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration13" / name

    def make_plan(
        self,
        root: str,
        edition_date: str = DATE,
        mode: str = "synthetic",
        *,
        planned: bool = False,
    ):
        h = self.helper()
        h.make_preflight(root, edition_date, mode, qualified=planned)
        kwargs = {}
        if planned:
            kwargs["integration_plan_fixture_root"] = h.fixture("synthetic-planned")
        run = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            integration_plan_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, edition_date, mode=mode)

    def locked_digests(self, engine: RunEngine):
        values = self.helper().locked_digests(engine)
        values["production-integration-plan"] = engine.store.load_artifact(
            "production-integration-plan"
        )["content_digest"]
        return values

    def write_fixture(
        self,
        root: Path,
        *,
        source: str = "synthetic-authorization-ready",
        policy_mutator=None,
        manifest_mutator=None,
    ) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        policy = json.loads((self.fixture(source) / "admission-policy.json").read_text())
        manifest = json.loads((self.fixture(source) / "admission-manifest.json").read_text())
        if policy_mutator:
            policy_mutator(policy)
        if manifest_mutator:
            manifest_mutator(manifest)
        (root / "admission-policy.json").write_text(json.dumps(policy))
        (root / "admission-manifest.json").write_text(json.dumps(manifest))
        return root

    def test_current_blocked_plan_cannot_silently_become_authorization_ready(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_plan(td)
            before_digests = self.locked_digests(engine)
            run = start_daily_brief(self.DATE, state_root=td, integration_admission_only=True)
            final = RunEngine(td, self.DATE)
            artifact = final.store.load_artifact("production-integration-admission")
            data = artifact["data"]
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(run["completion_status"], "complete_locked")
            self.assertEqual(data["plan_classification"], "blocked")
            self.assertEqual(data["classification"], "blocked")
            self.assertNotEqual(data["classification"], "authorization_ready")
            self.assertEqual(data["classification_reason_codes"][0], "ITERATION12_PLAN_BLOCKED")
            self.assertEqual(len(list(final.store.run_dir.glob("production-integration-admission.json"))), 1)
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)

    def test_synthetic_planned_plan_alone_is_insufficient_without_admission_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            start_daily_brief(self.DATE, state_root=td, integration_admission_only=True)
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-admission"
            )["data"]
            self.assertEqual(data["plan_classification"], "planned")
            self.assertEqual(data["classification"], "blocked")
            self.assertIn("ADMISSION_DISCOVERY_ADAPTER_MISSING", data["classification_reason_codes"])
            self.assertIn("ADMISSION_DECISION_MISSING", data["classification_reason_codes"])
            self.assertFalse(data["production_action_authorized"])

    def test_planned_plan_with_complete_evidence_but_no_separate_decision_remains_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            fixture = self.write_fixture(
                Path(td) / "no-decision",
                manifest_mutator=lambda m: m.__setitem__("admission_decision", None),
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=fixture,
                integration_admission_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-admission"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertEqual(data["classification_reason_codes"], ["ADMISSION_DECISION_MISSING"])
            self.assertIsNone(data["admission_decision_id"])

    def test_complete_synthetic_admission_is_logically_authorization_ready_only(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                integration_admission_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-admission"
            )["data"]
            self.assertEqual(data["plan_classification"], "planned")
            self.assertEqual(data["classification"], "authorization_ready")
            self.assertEqual(
                data["classification_reason_codes"],
                ["ADMISSION_INPUTS_COMPLETE_SYNTHETIC_ONLY"],
            )
            self.assertEqual(data["admission_decision_id"], "synthetic-admission-decision-v1")
            self.assertTrue(data["synthetic_only"])
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

    def test_admission_binds_exact_plan_graph_and_transitive_upstream_identities(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                integration_admission_only=True,
            )
            engine = RunEngine(td, self.DATE)
            admission = engine.store.load_artifact("production-integration-admission")
            plan = engine.store.load_artifact("production-integration-plan")
            preflight = engine.store.load_artifact("production-integration-preflight")
            readiness = engine.store.load_artifact("readiness-admission")
            completion = engine.store.load_artifact("completion")
            data = admission["data"]
            self.assertEqual(admission["input_digests"], [plan["content_digest"]])
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

    def test_admission_identity_is_deterministic_and_replay_reuses_exactly_one_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            kwargs = {
                "integration_admission_fixture_root": self.fixture("synthetic-authorization-ready"),
                "integration_admission_only": True,
            }
            first = start_daily_brief(self.DATE, state_root=td, **kwargs)
            engine = RunEngine(td, self.DATE)
            artifact1 = engine.store.load_artifact("production-integration-admission")
            counts = deepcopy(first["stage_executions"])
            second = start_daily_brief(self.DATE, state_root=td, **kwargs)
            artifact2 = engine.store.load_artifact("production-integration-admission")
            self.assertEqual(artifact2["content_digest"], artifact1["content_digest"])
            self.assertEqual(artifact2["data"]["admission_id"], artifact1["data"]["admission_id"])
            self.assertEqual(second["stage_executions"], counts)
            self.assertEqual(
                len(list(engine.store.run_dir.glob("production-integration-admission.json"))), 1
            )

    def test_admission_does_not_reexecute_or_rebuild_any_locked_iteration1_12_work(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_plan(td, planned=True)
            before_digests = self.locked_digests(engine)
            plan_state_path = engine.store.run_dir / "iteration12-plan-state.json"
            plan_state_before = engine.store.read_json(plan_state_path)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                integration_admission_only=True,
            )
            final = RunEngine(td, self.DATE)
            plan_state_after = final.store.read_json(plan_state_path)
            self.assertEqual(
                plan_state_after["attempts"]["plan_compilation"],
                plan_state_before["attempts"]["plan_compilation"],
            )
            self.assertEqual(
                plan_state_after["attempts"]["artifact_assembly"],
                plan_state_before["attempts"]["artifact_assembly"],
            )
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)
            metrics = final.store.read_json(final.store.run_dir / "iteration13-admission-metrics.json")
            self.assertEqual(metrics["anti_rework"]["locked_iterations_1_12_reexecution"], 0)
            self.assertEqual(metrics["anti_rework"]["iteration12_plan_compilation_reexecution"], 0)
            self.assertEqual(metrics["anti_rework"]["iteration12_plan_artifact_rebuild"], 0)
            self.assertEqual(metrics["anti_rework"]["full_pipeline_restarts"], 0)

    def test_corrupted_or_stale_iteration12_plan_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-plan")
            artifact = engine.store.read_json(path)
            artifact["data"]["classification"] = "blocked"
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationAdmissionError):
                start_daily_brief(self.DATE, state_root=td, integration_admission_only=True)

        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-plan")
            artifact = engine.store.read_json(path)
            artifact["data"]["completion_scope"] = "stale_scope"
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationAdmissionError):
                start_daily_brief(self.DATE, state_root=td, integration_admission_only=True)

    def test_unsupported_admission_policy_or_schema_version_fails_closed(self):
        for field in ("integration_admission_policy_version", "schema_version"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                self.make_plan(td, planned=True)
                fixture = self.write_fixture(
                    Path(td) / f"bad-{field}",
                    policy_mutator=lambda p, field=field: p.__setitem__(field, "9.9.9"),
                )
                with self.assertRaises(IntegrationAdmissionError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_admission_fixture_root=fixture,
                        integration_admission_only=True,
                    )

    def test_changed_plan_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-plan")
            artifact = engine.store.read_json(path)
            artifact["data"]["plan_id"] = "sha256:changed-plan-identity"
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationAdmissionError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                    integration_admission_only=True,
                )

    def test_changed_admission_policy_identity_fails_closed_instead_of_reusing_cache(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            ready = self.fixture("synthetic-authorization-ready")
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=ready,
                integration_admission_only=True,
            )
            changed = self.write_fixture(
                Path(td) / "changed-policy",
                policy_mutator=lambda p: p.__setitem__("policy_note", "identity-changed"),
            )
            with self.assertRaises(IntegrationAdmissionError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_admission_fixture_root=changed,
                    integration_admission_only=True,
                )

    def test_changed_admission_manifest_identity_fails_closed_instead_of_reusing_cache(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            ready = self.fixture("synthetic-authorization-ready")
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=ready,
                integration_admission_only=True,
            )
            changed = self.write_fixture(
                Path(td) / "changed-manifest",
                manifest_mutator=lambda m: m.__setitem__("manifest_note", "identity-changed"),
            )
            with self.assertRaises(IntegrationAdmissionError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_admission_fixture_root=changed,
                    integration_admission_only=True,
                )

    def test_missing_required_admission_inputs_remain_blocked(self):
        cases = {
            "discovery_adapter": "ADMISSION_DISCOVERY_ADAPTER_MISSING",
            "publication_target": "ADMISSION_PUBLICATION_TARGET_MISSING",
            "public_deployment_verification": "ADMISSION_PUBLIC_DEPLOYMENT_VERIFICATION_MISSING",
            "private_command_center": "ADMISSION_PRIVATE_COMMAND_CENTER_MISSING",
            "production_schedules": "ADMISSION_PRODUCTION_SCHEDULES_MISSING",
            "subscriber_delivery": "ADMISSION_SUBSCRIBER_DELIVERY_POLICY_MISSING",
            "migration_prerequisites": "ADMISSION_MIGRATION_PREREQUISITES_MISSING",
            "rollback_restore": "ADMISSION_ROLLBACK_RESTORE_MISSING",
            "zero_incremental_cost": "ADMISSION_ZERO_INCREMENTAL_COST_APPROVAL_MISSING",
        }
        for key, reason in cases.items():
            with self.subTest(key=key), tempfile.TemporaryDirectory() as td:
                self.make_plan(td, planned=True)
                fixture = self.write_fixture(
                    Path(td) / f"missing-{key}",
                    manifest_mutator=lambda m, key=key: m["evidence"].__setitem__(key, None),
                )
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_admission_fixture_root=fixture,
                    integration_admission_only=True,
                )
                data = RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-admission"
                )["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertIn(reason, data["classification_reason_codes"])

    def test_paid_dependency_without_zero_incremental_cost_guard_remains_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            def mutate(manifest):
                record = manifest["evidence"]["zero_incremental_cost"]
                record["zero_incremental_cost"] = False
                record["paid_deployment_or_hosting_api_required"] = True
            fixture = self.write_fixture(Path(td) / "paid-dependency", manifest_mutator=mutate)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=fixture,
                integration_admission_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-admission"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            self.assertIn("ZERO_INCREMENTAL_COST_GUARD_FAILED", data["classification_reason_codes"])

    def test_incomplete_iteration12_operational_closure_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_plan(td, planned=True)
            fixture = self.write_fixture(
                Path(td) / "closure-pending",
                manifest_mutator=lambda m: m["iteration12_closure"].__setitem__(
                    "repository_closure_status", "pending"
                ),
            )
            with self.assertRaises(IntegrationAdmissionError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_admission_fixture_root=fixture,
                    integration_admission_only=True,
                )

    def test_admission_evaluation_failure_recovers_on_fresh_engine_without_upstream_rework(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_plan(td, planned=True)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_admission_evaluation_failure",
                    "admission:evaluation",
                ),
                integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                integration_admission_only=True,
            )
            with self.assertRaises(IntegrationAdmissionBoundaryFailure):
                failing.run()
            self.assertIsNone(failing.store.load_artifact("production-integration-admission"))
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                integration_admission_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(fresh.store.run_dir / "iteration13-admission-state.json")
            incident = fresh.store.read_json(fresh.store.run_dir / "iteration13-admission-incident.json")
            self.assertEqual(state["attempts"]["admission_evaluation"], 2)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "evaluation")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_final_admission_artifact_failure_reuses_durable_evaluation_on_fresh_engine(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_plan(td, planned=True)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_final_admission_artifact_failure",
                    "admission:final_admission_artifact",
                ),
                integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                integration_admission_only=True,
            )
            with self.assertRaises(IntegrationAdmissionBoundaryFailure):
                failing.run()
            state_after_failure = failing.store.read_json(
                failing.store.run_dir / "iteration13-admission-state.json"
            )
            self.assertIsNotNone(state_after_failure["evaluation"])
            self.assertIsNone(failing.store.load_artifact("production-integration-admission"))
            recovered = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_admission_fixture_root=self.fixture("synthetic-authorization-ready"),
                integration_admission_only=True,
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(fresh.store.run_dir / "iteration13-admission-state.json")
            incident = fresh.store.read_json(fresh.store.run_dir / "iteration13-admission-incident.json")
            self.assertEqual(state["attempts"]["admission_evaluation"], 1)
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state["metrics"]["admission_evaluation_reuse"], 1)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(
                incident["recovery_receipt"]["boundary_id"], "final_admission_artifact"
            )
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_admission_contract_schema_is_versioned_and_non_authorizing(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-admission.schema.json"
            ).read_text()
        )
        self.assertEqual(schema["properties"]["admission_schema_version"]["const"], "1.0.0")
        self.assertEqual(schema["properties"]["admission_policy_version"]["const"], "1.0.0")
        self.assertEqual(
            schema["properties"]["classification"]["enum"],
            ["blocked", "authorization_ready", "invalid"],
        )
        self.assertFalse(schema["properties"]["production_action_authorized"]["const"])
        self.assertFalse(schema["properties"]["production_cutover_authorized"]["const"])
        self.assertFalse(schema["properties"]["legacy_decommission_authorized"]["const"])
        self.assertFalse(schema["properties"]["production_publication"]["const"])

    def test_admission_only_requires_complete_locked_and_cannot_combine_with_other_bounded_modes(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(self.DATE, state_root=td, integration_admission_only=True)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_plan_only=True,
                    integration_admission_only=True,
                )

    def test_three_consecutive_shadow_admission_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                before_counts, engine = self.make_plan(td, edition_date, mode="shadow")
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_admission_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow")
                artifact = final.store.load_artifact("production-integration-admission")
                data = artifact["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(data["classification_reason_codes"][0], "ITERATION12_PLAN_BLOCKED")
                self.assertEqual(
                    len(list(final.store.run_dir.glob("production-integration-admission.json"))), 1
                )
                self.assertEqual(self.locked_digests(final), before_digests)
                for stage, count in before_counts.items():
                    self.assertEqual(run["stage_executions"].get(stage), count)
                for flag in (
                    "real_private_command_center_mutated",
                    "public_site_mutated",
                    "production_schedule_action",
                    "subscriber_delivery_changed",
                    "legacy_content_migrated",
                    "production_publication",
                ):
                    self.assertFalse(data[flag])
                observed.append(
                    (data["classification"], tuple(data["classification_reason_codes"]))
                )
        self.assertEqual(len(observed), 3)
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(observed[1], observed[2])


if __name__ == "__main__":
    unittest.main()
