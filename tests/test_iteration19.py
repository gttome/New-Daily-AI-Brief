from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_authority_readiness import (
    IntegrationExecutionAuthorityReadinessBoundaryFailure,
    IntegrationExecutionAuthorityReadinessError,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration18


class Iteration19ExecutionAuthorityReadinessTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration18.Iteration18ExecutionAuthorizationPackageTest(
            methodName="test_current_repository_stays_blocked_without_rework"
        )

    def fixture(self, name):
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration19" / name

    def make_package(self, root, date=DATE, mode="synthetic", ready=False):
        h = self.helper()
        _, engine = h.make_decision(root, date, mode, ready=ready)
        kwargs = {}
        if ready:
            kwargs["integration_execution_authorization_package_fixture_root"] = h.write_fixture(
                Path(root) / "i18-ready", engine
            )
        run = start_daily_brief(
            date,
            mode=mode,
            state_root=root,
            integration_execution_authorization_package_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, date, mode=mode)

    def locked(self, engine):
        values = self.helper().locked(engine)
        values["production-integration-execution-authorization-package"] = (
            engine.store.load_artifact(
                "production-integration-execution-authorization-package"
            )["content_digest"]
        )
        return values

    def package_validations(self, engine):
        return [
            engine.store.read_json(
                engine.store.run_dir / f"authorization-package-validation-{position:02d}.json"
            )
            for position in range(1, 11)
        ]

    def write_fixture(
        self,
        root,
        engine,
        include_record=True,
        mutate_policy=None,
        mutate_manifest=None,
        mutate_record=None,
    ):
        root.mkdir(parents=True, exist_ok=True)
        src = self.fixture("synthetic-execution-authority-ready")
        policy = json.loads((src / "authority-readiness-policy.json").read_text())
        manifest = json.loads((src / "authority-readiness-manifest.json").read_text())
        record = json.loads((src / "authority-readiness-record.json").read_text())
        package = engine.store.load_artifact(
            "production-integration-execution-authorization-package"
        )
        pd = package["data"]
        package_validations = self.package_validations(engine)
        package_set_digest = digest(package_validations)
        manifest["authorization_package_binding"].update(
            {
                "authorization_package_artifact_digest": package["content_digest"],
                "authorization_package_id": pd["authorization_package_id"],
                "authorization_package_policy_id": pd["authorization_package_policy_id"],
                "authorization_package_policy_digest": pd[
                    "authorization_package_policy_digest"
                ],
                "authorization_package_manifest_id": pd["authorization_package_manifest_id"],
                "authorization_package_manifest_digest": pd[
                    "authorization_package_manifest_digest"
                ],
                "separate_authorization_package_id": pd[
                    "separate_authorization_package_id"
                ],
                "separate_authorization_package_digest": pd[
                    "separate_authorization_package_digest"
                ],
                "source_provenance_validation_ids": pd[
                    "source_provenance_validation_ids"
                ],
                "source_provenance_validation_digests": pd[
                    "source_provenance_validation_digests"
                ],
                "source_provenance_validation_set_digest": pd[
                    "source_provenance_validation_set_digest"
                ],
                "package_provenance_validation_ids": pd[
                    "package_provenance_validation_ids"
                ],
                "package_provenance_validation_digests": pd[
                    "package_provenance_validation_digests"
                ],
                "package_provenance_validation_set_digest": package_set_digest,
            }
        )
        record.update(
            {
                "authorization_package_artifact_digest": package["content_digest"],
                "authorization_package_id": pd["authorization_package_id"],
                "authorization_package_policy_id": pd["authorization_package_policy_id"],
                "authorization_package_policy_digest": pd[
                    "authorization_package_policy_digest"
                ],
                "authorization_package_manifest_id": pd["authorization_package_manifest_id"],
                "authorization_package_manifest_digest": pd[
                    "authorization_package_manifest_digest"
                ],
                "separate_authorization_package_id": pd[
                    "separate_authorization_package_id"
                ],
                "separate_authorization_package_digest": pd[
                    "separate_authorization_package_digest"
                ],
                "source_provenance_validation_set_digest": pd[
                    "source_provenance_validation_set_digest"
                ],
                "package_provenance_validation_set_digest": package_set_digest,
                "authorization_decision_artifact_digest": pd[
                    "authorization_decision_artifact_digest"
                ],
                "authorization_decision_id": pd["authorization_decision_id"],
                "authorization_review_artifact_digest": pd[
                    "authorization_review_artifact_digest"
                ],
                "authorization_review_id": pd["authorization_review_id"],
                "execution_rehearsal_artifact_digest": pd[
                    "execution_rehearsal_artifact_digest"
                ],
                "execution_rehearsal_id": pd["execution_rehearsal_id"],
                "execution_attempt_id": pd["execution_attempt_id"],
                "execution_preflight_id": pd["execution_preflight_id"],
                "admission_id": pd["admission_id"],
                "plan_id": pd["plan_id"],
                "plan_graph_digest": pd["plan_graph_digest"],
                "dry_run_assertion_set_digest": pd["dry_run_assertion_set_digest"],
                "rollback_boundary_set_digest": pd["rollback_boundary_set_digest"],
                "preflight_id": pd["preflight_id"],
                "readiness_assessment_id": pd["readiness_assessment_id"],
                "final_completion_receipt_digest": pd[
                    "final_completion_receipt_digest"
                ],
                "canonical_chain_digest": pd["canonical_chain_digest"],
            }
        )
        if mutate_policy:
            mutate_policy(policy)
        if mutate_manifest:
            mutate_manifest(manifest)
        if mutate_record:
            mutate_record(record)
        body = deepcopy(record)
        body.pop("readiness_record_id", None)
        record["readiness_record_id"] = digest(body)
        (root / "authority-readiness-policy.json").write_text(json.dumps(policy))
        (root / "authority-readiness-manifest.json").write_text(json.dumps(manifest))
        if include_record:
            (root / "authority-readiness-record.json").write_text(json.dumps(record))
        return root

    def data(self, root, date=DATE, mode="synthetic"):
        return RunEngine(root, date, mode=mode).store.load_artifact(
            "production-integration-execution-authority-readiness"
        )["data"]

    def safe(self, data):
        flags = (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_executor_invocation_authorized",
            "credentials_use_authorized",
            "real_target_contact_authorized",
            "rollback_execution_authorized",
            "real_private_command_center_mutated",
            "public_site_mutated",
            "production_schedule_action",
            "subscriber_delivery_changed",
            "legacy_content_migrated",
            "readers_routed_to_greenfield",
            "legacy_repository_modified",
            "incremental_paid_dependency_added",
            "lifecycle_state_changed",
        )
        self.assertTrue(all(data[name] is False for name in flags))
        self.assertEqual(
            (data["real_integration_steps_enabled"], data["real_integration_steps_executed"]),
            (0, 0),
        )
        self.assertTrue(all(item["enabled"] is False for item in data["execution_steps"]))

    def test_current_repository_stays_blocked_without_rework(self):
        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_package(td)
            locked = self.locked(engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authority_readiness_only=True,
            )
            data = self.data(td)
            self.assertEqual(data["classification"], "blocked")
            self.assertEqual(
                data["classification_reason_codes"][0],
                "ITERATION18_AUTHORIZATION_PACKAGE_BLOCKED",
            )
            self.assertEqual(data["readiness_provenance_validation_ids"], [])
            self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
            for key, value in counts.items():
                self.assertEqual(run["stage_executions"].get(key), value)
            self.safe(data)

    def test_ready_requires_separate_readiness_record_and_binds_exact_iteration18_chain(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_package(td, ready=True)
            fixture = self.write_fixture(
                Path(td) / "missing-readiness", engine, include_record=False
            )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authority_readiness_fixture_root=fixture,
                integration_execution_authority_readiness_only=True,
            )
            self.assertEqual(
                self.data(td)["classification_reason_codes"],
                ["EXECUTION_AUTHORITY_READINESS_RECORD_MISSING"],
            )

        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_package(td, ready=True)
            locked = self.locked(engine)
            fixture = self.write_fixture(Path(td) / "ready", engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_authority_readiness_fixture_root=fixture,
                integration_execution_authority_readiness_only=True,
            )
            data = self.data(td)
            package = engine.store.load_artifact(
                "production-integration-execution-authorization-package"
            )
            pd = package["data"]
            self.assertEqual(data["classification"], "execution_authority_ready")
            self.assertEqual(
                data["classification_reason_codes"],
                ["SYNTHETIC_EXECUTION_AUTHORITY_READY"],
            )
            self.assertEqual(
                data["authorization_package_artifact_digest"], package["content_digest"]
            )
            self.assertEqual(data["authorization_package_id"], pd["authorization_package_id"])
            self.assertEqual(
                data["separate_authorization_package_id"],
                pd["separate_authorization_package_id"],
            )
            self.assertEqual(len(data["source_provenance_validation_ids"]), 10)
            self.assertEqual(len(data["package_provenance_validation_ids"]), 10)
            self.assertEqual(len(data["readiness_provenance_validation_ids"]), 10)
            for field in (
                "authorization_decision_id",
                "authorization_review_id",
                "execution_rehearsal_id",
                "execution_attempt_id",
                "execution_preflight_id",
                "admission_id",
                "plan_id",
                "plan_graph_digest",
                "dry_run_assertion_set_digest",
                "rollback_boundary_set_digest",
                "preflight_id",
                "readiness_assessment_id",
                "final_completion_receipt_digest",
                "canonical_chain_digest",
            ):
                self.assertEqual(data[field], pd[field])
            self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
            for key, value in counts.items():
                self.assertEqual(run["stage_executions"].get(key), value)
            self.safe(data)

    def test_deterministic_replay_and_zero_iteration18_rebuild(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_package(td, ready=True)
            fixture = self.write_fixture(Path(td) / "replay", engine)
            kwargs = dict(
                state_root=td,
                integration_execution_authority_readiness_fixture_root=fixture,
                integration_execution_authority_readiness_only=True,
            )
            start_daily_brief(self.DATE, **kwargs)
            fresh = RunEngine(td, self.DATE)
            first = fresh.store.load_artifact(
                "production-integration-execution-authority-readiness"
            )
            package_digest = fresh.store.load_artifact(
                "production-integration-execution-authorization-package"
            )["content_digest"]
            start_daily_brief(self.DATE, **kwargs)
            second = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-authority-readiness"
            )
            self.assertEqual(first["content_digest"], second["content_digest"])
            self.assertEqual(first["data"], second["data"])
            self.assertEqual(
                RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-authorization-package"
                )["content_digest"],
                package_digest,
            )
            state = RunEngine(td, self.DATE).store.read_json(
                RunEngine(td, self.DATE).store.run_dir / "authority-readiness-state.json"
            )
            self.assertGreaterEqual(state["metrics"]["artifact_reuse"], 1)

    def test_fail_closed_stale_provenance_versions_bindings_steps_authority_and_cost(self):
        source_cases = (
            "package-policy-identity",
            "package-manifest-identity",
            "separate-package-identity",
            "package-schema",
            "reorder",
            "duplicate",
            "corrupt-validation",
            "step",
        )
        for case in source_cases:
            with self.subTest(source=case), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_package(td, ready=True)
                if case in {
                    "package-policy-identity",
                    "package-manifest-identity",
                    "separate-package-identity",
                    "package-schema",
                    "step",
                }:
                    artifact = engine.store.load_artifact(
                        "production-integration-execution-authorization-package"
                    )
                    data = artifact["data"]
                    if case == "package-policy-identity":
                        data["authorization_package_policy_id"] = "changed"
                    elif case == "package-manifest-identity":
                        data["authorization_package_manifest_id"] = "changed"
                    elif case == "separate-package-identity":
                        data["separate_authorization_package_id"] = "sha256:" + "0" * 64
                    elif case == "package-schema":
                        data["authorization_package_schema_version"] = "2.0.0"
                    else:
                        data["execution_steps"][0]["enabled"] = True
                    if case in {"package-schema", "step"}:
                        identity = {
                            key: deepcopy(value)
                            for key, value in data.items()
                            if key
                            not in {
                                "authorization_package_id",
                                "real_integration_steps_enabled",
                                "real_integration_steps_executed",
                                "final_state",
                                "final_status",
                                "completion_scope",
                                "synthetic_only",
                                "production_action_authorized",
                                "production_cutover_authorized",
                                "legacy_decommission_authorized",
                                "production_publication",
                                "real_executor_invocation_authorized",
                                "credentials_use_authorized",
                                "real_target_contact_authorized",
                                "rollback_execution_authorized",
                                "real_private_command_center_mutated",
                                "public_site_mutated",
                                "production_schedule_action",
                                "subscriber_delivery_changed",
                                "legacy_content_migrated",
                                "readers_routed_to_greenfield",
                                "legacy_repository_modified",
                                "incremental_paid_dependency_added",
                                "lifecycle_state_changed",
                            }
                        }
                        data["authorization_package_id"] = digest(identity)
                    artifact["content_digest"] = semantic_digest(artifact)
                    engine.store._atomic_write(
                        engine.store.artifact_path(
                            "production-integration-execution-authorization-package"
                        ),
                        artifact,
                    )
                elif case in {"reorder", "duplicate"}:
                    p1 = engine.store.run_dir / "authorization-package-validation-01.json"
                    p2 = engine.store.run_dir / "authorization-package-validation-02.json"
                    one = engine.store.read_json(p1)
                    two = engine.store.read_json(p2)
                    if case == "reorder":
                        engine.store._atomic_write(p1, two)
                        engine.store._atomic_write(p2, one)
                    else:
                        engine.store._atomic_write(p2, one)
                else:
                    p = engine.store.run_dir / "authorization-package-validation-01.json"
                    item = engine.store.read_json(p)
                    item["noop_verified"] = False
                    engine.store._atomic_write(p, item)
                with self.assertRaises(IntegrationExecutionAuthorityReadinessError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_authority_readiness_only=True,
                    )

        fixture_cases = (
            "bad-schema",
            "bad-policy",
            "changed-package-binding",
            "changed-manifest-identity",
            "bad-readiness-record-version",
            "changed-readiness-binding",
            "cost",
        )
        for case in fixture_cases:
            with self.subTest(fixture=case), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_package(td, ready=True)
                policy_mutation = None
                manifest_mutation = None
                record_mutation = None
                if case == "bad-schema":
                    policy_mutation = lambda p: p.update({"schema_version": "2.0.0"})
                elif case == "bad-policy":
                    policy_mutation = lambda p: p.update(
                        {"execution_authority_readiness_policy_version": "2.0.0"}
                    )
                elif case == "changed-package-binding":
                    manifest_mutation = lambda m: m["authorization_package_binding"].update(
                        {"authorization_package_id": "changed"}
                    )
                elif case == "changed-manifest-identity":
                    manifest_mutation = lambda m: m.update({"manifest_id": "changed"})
                elif case == "bad-readiness-record-version":
                    record_mutation = lambda r: r.update({"readiness_record_version": "2.0.0"})
                elif case == "changed-readiness-binding":
                    record_mutation = lambda r: r.update(
                        {"authorization_package_id": "changed"}
                    )
                else:
                    manifest_mutation = lambda m: m["evidence"]["cost_declaration"].update(
                        {
                            "incremental_paid_dependency_required": True,
                            "zero_incremental_cost_approved": False,
                        }
                    )
                fixture = self.write_fixture(
                    Path(td) / case,
                    engine,
                    mutate_policy=policy_mutation,
                    mutate_manifest=manifest_mutation,
                    mutate_record=record_mutation,
                )
                with self.assertRaises(IntegrationExecutionAuthorityReadinessError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_authority_readiness_fixture_root=fixture,
                        integration_execution_authority_readiness_only=True,
                    )

        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_executor_invocation_authorized",
            "credentials_use_authorized",
            "real_target_contact_authorized",
            "rollback_execution_authorized",
        ):
            with self.subTest(authority_flag=flag), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_package(td, ready=True)
                fixture = self.write_fixture(
                    Path(td) / flag,
                    engine,
                    mutate_manifest=lambda m, name=flag: m["evidence"][
                        "authority_state"
                    ].update({name: True}),
                )
                with self.assertRaises(IntegrationExecutionAuthorityReadinessError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_authority_readiness_fixture_root=fixture,
                        integration_execution_authority_readiness_only=True,
                    )

    def recovery(self, boundary):
        temp = tempfile.TemporaryDirectory()
        root = temp.name
        counts, engine = self.make_package(root, ready=True)
        locked = self.locked(engine)
        fixture = self.write_fixture(Path(root) / "recovery", engine)
        failing = RunEngine(
            root,
            self.DATE,
            failure_injection=FailureInjection("Complete", "synthetic_i19_failure", boundary),
            integration_execution_authority_readiness_fixture_root=fixture,
            integration_execution_authority_readiness_only=True,
        )
        with self.assertRaises(IntegrationExecutionAuthorityReadinessBoundaryFailure):
            failing.run()
        start_daily_brief(
            self.DATE,
            state_root=root,
            integration_execution_authority_readiness_fixture_root=fixture,
            integration_execution_authority_readiness_only=True,
        )
        fresh = RunEngine(root, self.DATE)
        self.assertEqual(self.locked(fresh), locked)
        for key, value in counts.items():
            self.assertEqual(fresh.store.load_run()["stage_executions"].get(key), value)
        self.assertEqual(
            fresh.store.read_json(
                fresh.store.run_dir / "authority-readiness-incident.json"
            )["result"],
            "recovered",
        )
        return temp, fresh

    def test_targeted_failure_recovery_and_fresh_engine_resume(self):
        temp, engine = self.recovery("authority_readiness:evaluation")
        state = engine.store.read_json(engine.store.run_dir / "authority-readiness-state.json")
        self.assertEqual(state["attempts"]["evaluation"], 2)
        temp.cleanup()

        temp, engine = self.recovery("authority_readiness:validation:5")
        state = engine.store.read_json(engine.store.run_dir / "authority-readiness-state.json")
        self.assertGreaterEqual(state["metrics"]["provenance_validation_reuse"], 4)
        self.assertEqual(len(self.data(temp.name)["readiness_provenance_validation_ids"]), 10)
        temp.cleanup()

        temp, engine = self.recovery(
            "authority_readiness:final_authority_readiness_artifact"
        )
        state = engine.store.read_json(engine.store.run_dir / "authority-readiness-state.json")
        self.assertEqual(state["attempts"]["artifact_assembly"], 2)
        self.assertGreaterEqual(state["metrics"]["provenance_validation_reuse"], 10)
        temp.cleanup()

    def test_bounded_exclusive_production_fail_closed_and_schema(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_authority_readiness_only=True,
                )
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_authorization_package_only=True,
                    integration_execution_authority_readiness_only=True,
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_authority_readiness_only=True,
                )
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-authority-readiness.schema.json"
            ).read_text()
        )
        for key in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_executor_invocation_authorized",
            "credentials_use_authorized",
            "real_target_contact_authorized",
            "rollback_execution_authorized",
        ):
            self.assertFalse(schema["properties"][key]["const"])

    def test_three_run_exit_gate_and_three_ready_proofs(self):
        blocked = []
        for date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                counts, engine = self.make_package(td, date, "shadow")
                locked = self.locked(engine)
                run = start_daily_brief(
                    date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_authority_readiness_only=True,
                )
                data = self.data(td, date, "shadow")
                self.safe(data)
                self.assertEqual(
                    self.locked(RunEngine(td, date, mode="shadow")), locked
                )
                for key, value in counts.items():
                    self.assertEqual(run["stage_executions"].get(key), value)
                blocked.append(
                    (data["classification"], tuple(data["classification_reason_codes"]))
                )
        self.assertEqual(blocked[0], blocked[1])
        self.assertEqual(blocked[1], blocked[2])

        ready = []
        for date in ("2026-09-25", "2026-09-26", "2026-09-27"):
            with tempfile.TemporaryDirectory() as td:
                _, engine = self.make_package(td, date, "shadow", ready=True)
                fixture = self.write_fixture(Path(td) / "ready", engine)
                start_daily_brief(
                    date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_authority_readiness_fixture_root=fixture,
                    integration_execution_authority_readiness_only=True,
                )
                data = self.data(td, date, "shadow")
                self.safe(data)
                self.assertEqual(data["classification"], "execution_authority_ready")
                self.assertTrue(
                    data["separate_execution_authority_readiness_id"].startswith("sha256:")
                )
                ready.append(
                    (data["classification"], tuple(data["classification_reason_codes"]))
                )
        self.assertEqual(ready[0], ready[1])
        self.assertEqual(ready[1], ready[2])


if __name__ == "__main__":
    unittest.main()
