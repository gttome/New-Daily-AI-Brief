from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_plan import (
    IntegrationPlanBoundaryFailure,
    IntegrationPlanError,
)
from new_daily_ai_brief.store import semantic_digest
import test_iteration11


class Iteration12IntegrationPlanTest(unittest.TestCase):
    DATE = "2026-09-22"
    BLOCKED_CODES = test_iteration11.Iteration11IntegrationPreflightTest.UNRESOLVED_CODES

    def helper(self):
        return test_iteration11.Iteration11IntegrationPreflightTest(
            methodName="test_current_repository_configuration_remains_unresolved"
        )

    def fixture(self, name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration12" / name

    def make_preflight(
        self,
        root: str,
        edition_date: str = DATE,
        mode: str = "synthetic",
        *,
        qualified: bool = False,
    ):
        self.helper().ready(root, edition_date, mode)
        kwargs = {}
        if qualified:
            kwargs["integration_preflight_fixture_root"] = self.fixture("synthetic-planned")
        run = start_daily_brief(
            edition_date,
            mode=mode,
            state_root=root,
            integration_preflight_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, edition_date, mode=mode)

    def locked_digests(self, engine: RunEngine):
        values = self.helper().locked_digests(engine)
        values["production-integration-preflight"] = engine.store.load_artifact(
            "production-integration-preflight"
        )["content_digest"]
        return values

    def write_fixture(
        self,
        root: Path,
        *,
        policy_mutator=None,
        manifest_name: str = "current-blocked",
    ) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        policy = json.loads(
            (self.fixture(manifest_name) / "integration-plan-policy.json").read_text()
        )
        if policy_mutator:
            policy_mutator(policy)
        manifest = json.loads(
            (self.fixture(manifest_name) / "resolution-manifest.json").read_text()
        )
        (root / "integration-plan-policy.json").write_text(json.dumps(policy))
        (root / "resolution-manifest.json").write_text(json.dumps(manifest))
        return root

    def test_current_unresolved_preflight_is_dedicatedly_blocked_and_never_planned(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_preflight(td)
            before_digests = self.locked_digests(engine)
            result = start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            final = RunEngine(td, self.DATE)
            artifact = final.store.load_artifact("production-integration-plan")
            data = artifact["data"]
            self.assertEqual(result["current_state"], "Complete")
            self.assertEqual(result["completion_status"], "complete_locked")
            self.assertEqual(data["preflight_classification"], "unresolved")
            self.assertEqual(data["classification"], "blocked")
            self.assertNotEqual(data["classification"], "planned")
            self.assertEqual(data["classification_reason_codes"], self.BLOCKED_CODES)
            self.assertEqual(len(data["plan_steps"]), 10)
            self.assertEqual(
                [x["step_state"] for x in data["plan_steps"]].count("planned"), 2
            )
            self.assertEqual(
                [x["step_state"] for x in data["plan_steps"]].count("blocked"), 8
            )
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(result["stage_executions"].get(stage), count)

    def test_fully_qualified_synthetic_preflight_compiles_complete_planned_graph_only(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td, qualified=True)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_plan_fixture_root=self.fixture("synthetic-planned"),
                integration_plan_only=True,
            )
            engine = RunEngine(td, self.DATE)
            data = engine.store.load_artifact("production-integration-plan")["data"]
            self.assertEqual(data["preflight_classification"], "qualified")
            self.assertEqual(data["classification"], "planned")
            self.assertEqual(data["classification_reason_codes"], ["PLAN_INPUTS_COMPLETE_SYNTHETIC_ONLY"])
            self.assertEqual(len(data["plan_steps"]), 10)
            self.assertTrue(all(x["step_state"] == "planned" for x in data["plan_steps"]))
            self.assertTrue(all(x["production_action_authorized"] is False for x in data["plan_steps"]))
            by_prerequisite = {x["prerequisite"]: x for x in data["plan_steps"]}
            self.assertEqual(
                by_prerequisite["production_discovery"]["explicit_references"]["adapter_id"],
                "synthetic-zero-cost-discovery-adapter",
            )
            self.assertEqual(
                by_prerequisite["production_publication"]["explicit_references"]["target_id"],
                "synthetic-publication-target",
            )
            self.assertEqual(
                by_prerequisite["public_deployment_verification"]["explicit_references"][
                    "verification_mechanism_id"
                ],
                "synthetic-route-verifier",
            )
            self.assertEqual(
                by_prerequisite["private_command_center"]["explicit_references"]["privacy_boundary"],
                "synthetic-owner-only",
            )
            schedules = by_prerequisite["production_schedules"]["explicit_references"]
            self.assertEqual(len(schedules["schedule_identities"]), 2)
            self.assertEqual(len(schedules["schedule_cadences"]), 2)
            migration = by_prerequisite["legacy_migration_cutover"]["explicit_references"]
            self.assertFalse(migration["cutover_authorized"])
            self.assertFalse(migration["legacy_decommission_authorized"])
            self.assertEqual(
                by_prerequisite["rollback_recovery"]["explicit_references"]["rollback_identity"],
                "synthetic-restore-point",
            )
            self.assertGreaterEqual(len(data["dry_run_assertion_set"]), 10)
            self.assertEqual(len(data["rollback_boundary_set"]), 10)

    def test_plan_binds_exact_locked_iteration11_preflight_and_upstream_identities(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td)
            start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            engine = RunEngine(td, self.DATE)
            preflight = engine.store.load_artifact("production-integration-preflight")
            readiness = engine.store.load_artifact("readiness-admission")
            plan = engine.store.load_artifact("production-integration-plan")
            data = plan["data"]
            self.assertEqual(plan["input_digests"], [preflight["content_digest"]])
            self.assertEqual(data["preflight_artifact_digest"], preflight["content_digest"])
            self.assertEqual(data["preflight_id"], preflight["data"]["preflight_id"])
            self.assertEqual(data["readiness_artifact_digest"], readiness["content_digest"])
            self.assertEqual(data["readiness_assessment_id"], readiness["data"]["assessment_id"])
            self.assertEqual(
                data["completion_artifact_digest"], readiness["data"]["completion_artifact_digest"]
            )
            self.assertEqual(
                data["final_completion_receipt_digest"],
                readiness["data"]["final_completion_receipt_digest"],
            )

    def test_plan_identity_is_deterministic_and_replay_reuses_exactly_one_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td)
            first = start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            engine = RunEngine(td, self.DATE)
            artifact1 = engine.store.load_artifact("production-integration-plan")
            counts = deepcopy(first["stage_executions"])
            second = start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            artifact2 = engine.store.load_artifact("production-integration-plan")
            self.assertEqual(artifact2["content_digest"], artifact1["content_digest"])
            self.assertEqual(artifact2["data"]["plan_id"], artifact1["data"]["plan_id"])
            self.assertEqual(second["stage_executions"], counts)
            self.assertEqual(
                len(list(engine.store.run_dir.glob("production-integration-plan.json"))), 1
            )

    def test_plan_does_not_reexecute_iteration11_or_any_locked_upstream_stage(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_preflight(td)
            before_digests = self.locked_digests(engine)
            preflight_state_path = engine.store.run_dir / "iteration11-preflight-state.json"
            preflight_state_before = engine.store.read_json(preflight_state_path)
            run = start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            preflight_state_after = engine.store.read_json(preflight_state_path)
            self.assertEqual(
                preflight_state_after["attempts"]["resolution_evaluation"],
                preflight_state_before["attempts"]["resolution_evaluation"],
            )
            self.assertEqual(self.locked_digests(engine), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)

    def test_corrupted_or_stale_preflight_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-preflight")
            artifact = engine.store.read_json(path)
            artifact["data"]["classification"] = "qualified"
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationPlanError):
                start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)

        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-preflight")
            artifact = engine.store.read_json(path)
            artifact["data"]["final_state"] = "Deployed"
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationPlanError):
                start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)

    def test_unsupported_plan_policy_or_schema_version_fails_closed(self):
        for field in ("integration_plan_policy_version", "schema_version"):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as td:
                self.make_preflight(td)
                fixture = Path(td) / "bad-plan-fixture"
                self.write_fixture(
                    fixture,
                    policy_mutator=lambda p, field=field: p.__setitem__(field, "9.9.9"),
                )
                with self.assertRaises(IntegrationPlanError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_plan_fixture_root=fixture,
                        integration_plan_only=True,
                    )

    def test_changed_preflight_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td)
            engine = RunEngine(td, self.DATE)
            path = engine.store.artifact_path("production-integration-preflight")
            artifact = engine.store.read_json(path)
            artifact["data"]["preflight_id"] = "sha256:changed-preflight-identity"
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(path, artifact)
            with self.assertRaises(IntegrationPlanError):
                start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)

    def test_changed_plan_policy_identity_fails_closed_instead_of_reusing_cached_plan(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td)
            start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            fixture = Path(td) / "changed-plan-policy"
            self.write_fixture(
                fixture,
                policy_mutator=lambda p: p.__setitem__("policy_id", "different-valid-plan-policy"),
            )
            with self.assertRaises(IntegrationPlanError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_plan_fixture_root=fixture,
                    integration_plan_only=True,
                )

    def test_missing_cost_adapter_target_schedule_and_rollback_inputs_remain_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td)
            start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-plan"
            )["data"]
            self.assertEqual(data["classification"], "blocked")
            for code in (
                "COST_POLICY_RESOLUTION_MISSING",
                "PRODUCTION_DISCOVERY_RESOLUTION_MISSING",
                "PRODUCTION_PUBLICATION_RESOLUTION_MISSING",
                "PUBLIC_DEPLOYMENT_VERIFICATION_RESOLUTION_MISSING",
                "PRIVATE_COMMAND_CENTER_RESOLUTION_MISSING",
                "PRODUCTION_SCHEDULES_RESOLUTION_MISSING",
                "LEGACY_MIGRATION_CUTOVER_RESOLUTION_MISSING",
                "ROLLBACK_RECOVERY_RESOLUTION_MISSING",
            ):
                self.assertIn(code, data["classification_reason_codes"])

    def test_plan_compilation_failure_recovers_on_fresh_engine_without_upstream_rework(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_preflight(td)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_plan_compilation_failure",
                    "plan:compilation",
                ),
                integration_plan_only=True,
            )
            with self.assertRaises(IntegrationPlanBoundaryFailure):
                failing.run()
            self.assertIsNone(failing.store.load_artifact("production-integration-plan"))
            recovered = start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(fresh.store.run_dir / "iteration12-plan-state.json")
            incident = fresh.store.read_json(fresh.store.run_dir / "iteration12-plan-incident.json")
            self.assertEqual(state["attempts"]["plan_compilation"], 2)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "compilation")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_final_plan_artifact_failure_reuses_durable_compilation_on_fresh_engine(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.make_preflight(td)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_final_plan_artifact_failure",
                    "plan:final_plan_artifact",
                ),
                integration_plan_only=True,
            )
            with self.assertRaises(IntegrationPlanBoundaryFailure):
                failing.run()
            self.assertIsNone(failing.store.load_artifact("production-integration-plan"))
            state_after_failure = failing.store.read_json(
                failing.store.run_dir / "iteration12-plan-state.json"
            )
            self.assertIsNotNone(state_after_failure["compiled_plan"])
            recovered = start_daily_brief(self.DATE, state_root=td, integration_plan_only=True)
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(fresh.store.run_dir / "iteration12-plan-state.json")
            incident = fresh.store.read_json(fresh.store.run_dir / "iteration12-plan-incident.json")
            self.assertEqual(state["attempts"]["plan_compilation"], 1)
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state["metrics"]["plan_compilation_reuse"], 1)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "final_plan_artifact")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_nonproduction_authorization_and_zero_incremental_cost_guards_are_fixed_false(self):
        with tempfile.TemporaryDirectory() as td:
            self.make_preflight(td, qualified=True)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_plan_fixture_root=self.fixture("synthetic-planned"),
                integration_plan_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-plan"
            )["data"]
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
            cost = {
                x["prerequisite"]: x for x in data["plan_steps"]
            }["cost_policy"]["explicit_references"]
            self.assertFalse(cost["separately_billed_openai_api_required"])
            self.assertFalse(cost["paid_completion_or_storage_api_required"])
            self.assertFalse(cost["paid_deployment_or_hosting_api_required"])
            self.assertFalse(cost["other_incremental_paid_dependency_required"])

    def test_plan_contract_schema_is_versioned_and_fail_closed(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-plan.schema.json"
            ).read_text()
        )
        self.assertEqual(schema["properties"]["plan_schema_version"]["const"], "1.0.0")
        self.assertEqual(schema["properties"]["plan_policy_version"]["const"], "1.0.0")
        self.assertEqual(
            schema["properties"]["classification"]["enum"], ["blocked", "planned", "invalid"]
        )
        self.assertFalse(schema["properties"]["production_action_authorized"]["const"])

    def test_three_consecutive_shadow_plan_only_exit_gate_runs(self):
        observed = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                before_counts, engine = self.make_preflight(td, edition_date, mode="shadow")
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_plan_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow")
                artifact = final.store.load_artifact("production-integration-plan")
                data = artifact["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(data["classification_reason_codes"], self.BLOCKED_CODES)
                self.assertEqual(len(list(final.store.run_dir.glob("production-integration-plan.json"))), 1)
                self.assertEqual(self.locked_digests(final), before_digests)
                for stage, count in before_counts.items():
                    self.assertEqual(run["stage_executions"].get(stage), count)
                for flag in (
                    "real_private_command_center_mutated",
                    "public_site_mutated",
                    "production_schedule_action",
                    "legacy_content_migrated",
                    "production_publication",
                ):
                    self.assertFalse(data[flag])
                observed.append((data["classification"], data["classification_reason_codes"]))
        self.assertEqual(observed, [("blocked", self.BLOCKED_CODES)] * 3)


if __name__ == "__main__":
    unittest.main()
