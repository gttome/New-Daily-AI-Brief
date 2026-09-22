from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_executor_binding_readiness import (
    IntegrationExecutionExecutorBindingReadinessBoundaryFailure,
    IntegrationExecutionExecutorBindingReadinessError,
    ProductionIntegrationExecutionExecutorBindingReadiness,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration19


class Iteration20ExecutorBindingReadinessTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration19.Iteration19ExecutionAuthorityReadinessTest(
            methodName="test_current_repository_stays_blocked_without_rework"
        )

    def fixture(self, name):
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration20" / name

    def make_authority_readiness(
        self, root, date=DATE, mode="synthetic", ready=False
    ):
        h = self.helper()
        _, engine = h.make_package(root, date, mode, ready=ready)
        kwargs = {}
        if ready:
            kwargs["integration_execution_authority_readiness_fixture_root"] = (
                h.write_fixture(Path(root) / "i19-ready", engine)
            )
        run = start_daily_brief(
            date,
            mode=mode,
            state_root=root,
            integration_execution_authority_readiness_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(
            root, date, mode=mode
        )

    def locked(self, engine):
        values = self.helper().locked(engine)
        values["production-integration-execution-authority-readiness"] = (
            engine.store.load_artifact(
                "production-integration-execution-authority-readiness"
            )["content_digest"]
        )
        return values

    def data(self, root, date=DATE, mode="synthetic"):
        return RunEngine(root, date, mode=mode).store.load_artifact(
            "production-integration-execution-executor-binding-readiness"
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
            "real_executor_bound",
            "real_executor_invoked",
            "production_credentials_present",
            "production_credentials_stored",
            "real_target_contacted",
            "rollback_executed",
            "cutover_executed",
            "decommission_executed",
            "publication_executed",
            "external_mutation_performed",
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
            (
                data["real_integration_steps_enabled"],
                data["real_integration_steps_executed"],
            ),
            (0, 0),
        )
        self.assertTrue(
            all(item["enabled"] is False for item in data["execution_steps"])
        )

    def write_fixture(
        self,
        root,
        engine,
        *,
        include_record=True,
        include_descriptor=True,
        mutate_policy=None,
        mutate_manifest=None,
        mutate_record=None,
        mutate_descriptor=None,
    ):
        root.mkdir(parents=True, exist_ok=True)
        src = self.fixture("synthetic-executor-binding-ready")
        policy = json.loads(
            (src / "executor-binding-readiness-policy.json").read_text()
        )
        manifest = json.loads(
            (src / "executor-binding-readiness-manifest.json").read_text()
        )
        record = json.loads(
            (src / "executor-binding-readiness-record.json").read_text()
        )
        descriptor = json.loads(
            (src / "synthetic-executor-descriptor.json").read_text()
        )
        gate = ProductionIntegrationExecutionExecutorBindingReadiness(
            engine.store,
            engine.edition_date,
            engine.mode,
            root,
        )
        context = gate._context(engine.store.load_run())
        bound = context["bound_upstream_identity"]

        if mutate_descriptor:
            mutate_descriptor(descriptor)
        descriptor_body = deepcopy(descriptor)
        descriptor_body.pop("descriptor_id", None)
        descriptor["descriptor_id"] = digest(descriptor_body)
        descriptor_binding = {
            "synthetic_executor_descriptor_id": descriptor["descriptor_id"],
            "synthetic_executor_descriptor_digest": digest(descriptor),
        }

        manifest["authority_readiness_binding"] = {
            "binding_mode": "exact_locked_execution_authority_readiness_artifact",
            "authority_readiness_artifact_digest": bound[
                "authority_readiness_artifact_digest"
            ],
            "execution_authority_readiness_id": bound[
                "execution_authority_readiness_id"
            ],
            "execution_authority_readiness_policy_id": bound[
                "execution_authority_readiness_policy_id"
            ],
            "execution_authority_readiness_policy_digest": bound[
                "execution_authority_readiness_policy_digest"
            ],
            "execution_authority_readiness_manifest_id": bound[
                "execution_authority_readiness_manifest_id"
            ],
            "execution_authority_readiness_manifest_digest": bound[
                "execution_authority_readiness_manifest_digest"
            ],
            "separate_execution_authority_readiness_id": bound[
                "separate_execution_authority_readiness_id"
            ],
            "separate_execution_authority_readiness_digest": bound[
                "separate_execution_authority_readiness_digest"
            ],
            "readiness_provenance_validation_ids": bound[
                "readiness_provenance_validation_ids"
            ],
            "readiness_provenance_validation_digests": bound[
                "readiness_provenance_validation_digests"
            ],
            "readiness_provenance_validation_set_digest": bound[
                "readiness_provenance_validation_set_digest"
            ],
            "bound_upstream_identity_digest": context[
                "bound_upstream_identity_digest"
            ],
        }
        manifest["executor_descriptor_binding"] = {
            "binding_mode": "exact_non_live_synthetic_executor_descriptor",
            **descriptor_binding,
        }

        record.update(
            {
                "authority_readiness_artifact_digest": bound[
                    "authority_readiness_artifact_digest"
                ],
                "execution_authority_readiness_id": bound[
                    "execution_authority_readiness_id"
                ],
                "execution_authority_readiness_policy_id": bound[
                    "execution_authority_readiness_policy_id"
                ],
                "execution_authority_readiness_policy_digest": bound[
                    "execution_authority_readiness_policy_digest"
                ],
                "execution_authority_readiness_manifest_id": bound[
                    "execution_authority_readiness_manifest_id"
                ],
                "execution_authority_readiness_manifest_digest": bound[
                    "execution_authority_readiness_manifest_digest"
                ],
                "separate_execution_authority_readiness_id": bound[
                    "separate_execution_authority_readiness_id"
                ],
                "separate_execution_authority_readiness_digest": bound[
                    "separate_execution_authority_readiness_digest"
                ],
                "source_provenance_validation_set_digest": bound[
                    "source_provenance_validation_set_digest"
                ],
                "package_provenance_validation_set_digest": bound[
                    "package_provenance_validation_set_digest"
                ],
                "readiness_provenance_validation_set_digest": bound[
                    "readiness_provenance_validation_set_digest"
                ],
                "canonical_chain_digest": bound["canonical_chain_digest"],
                "bound_upstream_identity_digest": context[
                    "bound_upstream_identity_digest"
                ],
                **descriptor_binding,
            }
        )

        if mutate_policy:
            mutate_policy(policy)
        if mutate_manifest:
            mutate_manifest(manifest)
        if mutate_record:
            mutate_record(record)

        record_body = deepcopy(record)
        record_body.pop("readiness_record_id", None)
        record["readiness_record_id"] = digest(record_body)

        (root / "executor-binding-readiness-policy.json").write_text(
            json.dumps(policy)
        )
        (root / "executor-binding-readiness-manifest.json").write_text(
            json.dumps(manifest)
        )
        if include_record:
            (root / "executor-binding-readiness-record.json").write_text(
                json.dumps(record)
            )
        if include_descriptor:
            (root / "synthetic-executor-descriptor.json").write_text(
                json.dumps(descriptor)
            )
        return root

    def clone_root(self, source, destination):
        shutil.copytree(source, destination, dirs_exist_ok=True)

    def test_current_repository_stays_blocked_deterministic_and_zero_rework(self):
        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_authority_readiness(td)
            locked = self.locked(engine)
            run = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_readiness_only=True,
            )
            data = self.data(td)
            self.assertEqual(data["classification"], "blocked")
            self.assertEqual(
                data["classification_reason_codes"][0],
                "ITERATION19_EXECUTION_AUTHORITY_READINESS_BLOCKED",
            )
            self.safe(data)
            first_digest = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-readiness"
            )["content_digest"]
            fresh = RunEngine(td, self.DATE)
            self.assertEqual(self.locked(fresh), locked)
            for key, value in counts.items():
                self.assertEqual(run["stage_executions"].get(key), value)
            replay = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_readiness_only=True,
            )
            second = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-readiness"
            )
            self.assertEqual(second["content_digest"], first_digest)
            self.assertEqual(
                second["data"]["executor_binding_readiness_id"],
                data["executor_binding_readiness_id"],
            )
            for key, value in counts.items():
                self.assertEqual(replay["stage_executions"].get(key), value)

    def test_execution_authority_ready_requires_separate_record_and_descriptor(self):
        with tempfile.TemporaryDirectory() as base:
            _, base_engine = self.make_authority_readiness(base, ready=True)
            source = base_engine.store.load_artifact(
                "production-integration-execution-authority-readiness"
            )
            self.assertEqual(
                source["data"]["classification"], "execution_authority_ready"
            )

            with tempfile.TemporaryDirectory() as td:
                self.clone_root(base, td)
                engine = RunEngine(td, self.DATE)
                fixture = self.write_fixture(Path(td) / "i20-ready", engine)
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_readiness_fixture_root=fixture,
                    integration_execution_executor_binding_readiness_only=True,
                )
                data = self.data(td)
                self.assertEqual(data["classification"], "executor_binding_ready")
                self.assertTrue(
                    data["separate_executor_binding_readiness_id"].startswith(
                        "sha256:"
                    )
                )
                self.assertTrue(
                    data["synthetic_executor_descriptor_id"].startswith(
                        "sha256:"
                    )
                )
                self.assertEqual(
                    len(data["executor_binding_provenance_validation_ids"]), 10
                )
                self.safe(data)

            for missing in ("record", "descriptor"):
                with self.subTest(missing=missing), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    fixture = self.write_fixture(
                        Path(td) / f"i20-missing-{missing}",
                        engine,
                        include_record=missing != "record",
                        include_descriptor=missing != "descriptor",
                    )
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_executor_binding_readiness_fixture_root=fixture,
                        integration_execution_executor_binding_readiness_only=True,
                    )
                    data = self.data(td)
                    self.assertEqual(data["classification"], "blocked")
                    expected = (
                        "EXECUTOR_BINDING_READINESS_RECORD_MISSING"
                        if missing == "record"
                        else "SYNTHETIC_EXECUTOR_DESCRIPTOR_MISSING"
                    )
                    self.assertEqual(
                        data["classification_reason_codes"][0], expected
                    )
                    self.safe(data)

    def test_fail_closed_source_identity_and_provenance_substitution(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_authority_readiness(base, ready=True)

            def expect_failure(mutator):
                with tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    mutator(engine)
                    with self.assertRaises(
                        IntegrationExecutionExecutorBindingReadinessError
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_readiness_only=True,
                        )

            def corrupt_artifact(engine):
                artifact = engine.store.load_artifact(
                    "production-integration-execution-authority-readiness"
                )
                artifact["data"][
                    "execution_authority_readiness_id"
                ] = "sha256:" + "0" * 64
                engine.store._atomic_write(
                    engine.store.artifact_path(
                        "production-integration-execution-authority-readiness"
                    ),
                    artifact,
                )

            expect_failure(corrupt_artifact)

            def reorder(engine):
                p1 = engine.store.run_dir / "authority-readiness-validation-01.json"
                p2 = engine.store.run_dir / "authority-readiness-validation-02.json"
                one = engine.store.read_json(p1)
                two = engine.store.read_json(p2)
                engine.store._atomic_write(p1, two)
                engine.store._atomic_write(p2, one)

            expect_failure(reorder)

            def duplicate(engine):
                p1 = engine.store.run_dir / "authority-readiness-validation-01.json"
                p2 = engine.store.run_dir / "authority-readiness-validation-02.json"
                engine.store._atomic_write(p2, engine.store.read_json(p1))

            expect_failure(duplicate)

            def changed_separate_identity(engine):
                artifact = engine.store.load_artifact(
                    "production-integration-execution-authority-readiness"
                )
                data = artifact["data"]
                data["separate_execution_authority_readiness_id"] = (
                    "sha256:" + "1" * 64
                )
                gate = ProductionIntegrationExecutionExecutorBindingReadiness(
                    engine.store,
                    self.DATE,
                    "synthetic",
                    self.fixture("current-blocked"),
                )
                data["execution_authority_readiness_id"] = digest(
                    gate._source_identity(data)
                )
                artifact["content_digest"] = semantic_digest(artifact)
                engine.store._atomic_write(
                    engine.store.artifact_path(
                        "production-integration-execution-authority-readiness"
                    ),
                    artifact,
                )

            expect_failure(changed_separate_identity)

    def test_fail_closed_iteration20_versions_identities_descriptor_and_authority(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_authority_readiness(base, ready=True)

            fixture_cases = {
                "schema": dict(
                    mutate_policy=lambda p: p.update({"schema_version": "2.0.0"})
                ),
                "policy-version": dict(
                    mutate_policy=lambda p: p.update(
                        {"executor_binding_readiness_policy_version": "2.0.0"}
                    )
                ),
                "policy-id": dict(
                    mutate_policy=lambda p: p.update({"policy_id": "changed"})
                ),
                "manifest-id": dict(
                    mutate_manifest=lambda m: m.update({"manifest_id": "changed"})
                ),
                "record-version": dict(
                    mutate_record=lambda r: r.update({"record_version": "2.0.0"})
                ),
                "record-binding": dict(
                    mutate_record=lambda r: r.update(
                        {"execution_authority_readiness_id": "changed"}
                    )
                ),
                "descriptor-version": dict(
                    mutate_descriptor=lambda d: d.update(
                        {"descriptor_version": "2.0.0"}
                    )
                ),
                "real-endpoint": dict(
                    mutate_descriptor=lambda d: d.update(
                        {"external_endpoint": "https://example.invalid/executor"}
                    )
                ),
                "invocable": dict(
                    mutate_descriptor=lambda d: d.update(
                        {"invocation_capability": True}
                    )
                ),
                "credential-ref": dict(
                    mutate_descriptor=lambda d: d.update(
                        {"credential_reference": "prod-credential"}
                    )
                ),
                "target-ref": dict(
                    mutate_descriptor=lambda d: d.update(
                        {"deployment_target": "production"}
                    )
                ),
                "paid-dependency": dict(
                    mutate_descriptor=lambda d: d.update(
                        {"paid_dependency_required": True}
                    )
                ),
                "production-authority": dict(
                    mutate_descriptor=lambda d: d.update(
                        {"production_authority_granted": True}
                    )
                ),
                "manifest-cost": dict(
                    mutate_manifest=lambda m: m["evidence"][
                        "cost_declaration"
                    ].update(
                        {
                            "incremental_paid_dependency_required": True,
                            "zero_incremental_cost_approved": False,
                        }
                    )
                ),
            }
            for name, kwargs in fixture_cases.items():
                with self.subTest(case=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    fixture = self.write_fixture(
                        Path(td) / name, engine, **kwargs
                    )
                    with self.assertRaises(
                        IntegrationExecutionExecutorBindingReadinessError
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_readiness_fixture_root=fixture,
                            integration_execution_executor_binding_readiness_only=True,
                        )

            for unsafe in ("step", "authority"):
                with self.subTest(source=unsafe), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    artifact = engine.store.load_artifact(
                        "production-integration-execution-authority-readiness"
                    )
                    data = artifact["data"]
                    if unsafe == "step":
                        data["execution_steps"][0]["enabled"] = True
                    else:
                        data["production_action_authorized"] = True
                    gate = ProductionIntegrationExecutionExecutorBindingReadiness(
                        engine.store,
                        self.DATE,
                        "synthetic",
                        self.fixture("current-blocked"),
                    )
                    data["execution_authority_readiness_id"] = digest(
                        gate._source_identity(data)
                    )
                    artifact["content_digest"] = semantic_digest(artifact)
                    engine.store._atomic_write(
                        engine.store.artifact_path(
                            "production-integration-execution-authority-readiness"
                        ),
                        artifact,
                    )
                    with self.assertRaises(
                        IntegrationExecutionExecutorBindingReadinessError
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_readiness_only=True,
                        )

    def recovery(self, source_root, boundary):
        temp = tempfile.TemporaryDirectory()
        root = temp.name
        self.clone_root(source_root, root)
        engine = RunEngine(root, self.DATE)
        counts = deepcopy(engine.store.load_run()["stage_executions"])
        locked = self.locked(engine)
        fixture = self.write_fixture(Path(root) / "recovery", engine)
        failing = RunEngine(
            root,
            self.DATE,
            failure_injection=FailureInjection(
                "Complete", "synthetic_i20_failure", boundary
            ),
            integration_execution_executor_binding_readiness_fixture_root=fixture,
            integration_execution_executor_binding_readiness_only=True,
        )
        with self.assertRaises(
            IntegrationExecutionExecutorBindingReadinessBoundaryFailure
        ):
            failing.run()
        start_daily_brief(
            self.DATE,
            state_root=root,
            integration_execution_executor_binding_readiness_fixture_root=fixture,
            integration_execution_executor_binding_readiness_only=True,
        )
        fresh = RunEngine(root, self.DATE)
        self.assertEqual(self.locked(fresh), locked)
        for key, value in counts.items():
            self.assertEqual(
                fresh.store.load_run()["stage_executions"].get(key), value
            )
        self.assertEqual(
            fresh.store.read_json(
                fresh.store.run_dir / "executor-binding-readiness-incident.json"
            )["result"],
            "recovered",
        )
        return temp, fresh

    def test_targeted_recovery_fresh_engine_no_rework(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_authority_readiness(base, ready=True)

            temp, engine = self.recovery(
                base, "executor_binding_readiness:evaluation"
            )
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-readiness-state.json"
            )
            self.assertEqual(state["attempts"]["evaluation"], 2)
            temp.cleanup()

            temp, engine = self.recovery(
                base, "executor_binding_readiness:validation:5"
            )
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-readiness-state.json"
            )
            self.assertGreaterEqual(
                state["metrics"]["provenance_validation_reuse"], 4
            )
            self.assertEqual(
                len(
                    self.data(temp.name)[
                        "executor_binding_provenance_validation_ids"
                    ]
                ),
                10,
            )
            temp.cleanup()

            temp, engine = self.recovery(
                base,
                "executor_binding_readiness:final_executor_binding_readiness_artifact",
            )
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-readiness-state.json"
            )
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(
                state["metrics"]["provenance_validation_reuse"], 10
            )
            temp.cleanup()

    def test_bounded_exclusive_production_fail_closed_and_schema(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_readiness_only=True,
                )
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_authority_readiness_only=True,
                    integration_execution_executor_binding_readiness_only=True,
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_executor_binding_readiness_only=True,
                )
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-executor-binding-readiness.schema.json"
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
            "real_executor_bound",
            "real_executor_invoked",
            "production_credentials_present",
            "production_credentials_stored",
            "real_target_contacted",
            "rollback_executed",
            "cutover_executed",
            "decommission_executed",
            "publication_executed",
            "external_mutation_performed",
        ):
            self.assertFalse(schema["properties"][key]["const"])

    def test_three_run_exit_gate_is_blocked_stable_and_independent(self):
        outcomes = []
        for date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                counts, engine = self.make_authority_readiness(
                    td, date, "shadow"
                )
                locked = self.locked(engine)
                run = start_daily_brief(
                    date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_executor_binding_readiness_only=True,
                )
                data = self.data(td, date, "shadow")
                self.safe(data)
                self.assertEqual(
                    self.locked(RunEngine(td, date, mode="shadow")), locked
                )
                for key, value in counts.items():
                    self.assertEqual(run["stage_executions"].get(key), value)
                outcomes.append(
                    (
                        data["classification"],
                        tuple(data["classification_reason_codes"]),
                        data["executor_binding_readiness_id"],
                    )
                )
        self.assertEqual(outcomes[0][0], "blocked")
        self.assertEqual(outcomes[0][0:2], outcomes[1][0:2])
        self.assertEqual(outcomes[1][0:2], outcomes[2][0:2])


if __name__ == "__main__":
    unittest.main()
