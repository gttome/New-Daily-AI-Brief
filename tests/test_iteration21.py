from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_executor_binding_preflight import (
    IntegrationExecutionExecutorBindingPreflightBoundaryFailure,
    IntegrationExecutionExecutorBindingPreflightError,
    ProductionIntegrationExecutionExecutorBindingPreflight,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration20


class Iteration21ExecutorBindingPreflightTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration20.Iteration20ExecutorBindingReadinessTest(
            methodName="test_current_repository_stays_blocked_deterministic_and_zero_rework"
        )

    def fixture(self, name):
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration21" / name

    def make_executor_binding_readiness(
        self, root, date=DATE, mode="synthetic", ready=False
    ):
        h = self.helper()
        _, engine = h.make_authority_readiness(root, date, mode, ready=ready)
        kwargs = {}
        if ready:
            kwargs["integration_execution_executor_binding_readiness_fixture_root"] = (
                h.write_fixture(Path(root) / "i20-ready", engine)
            )
        run = start_daily_brief(
            date,
            mode=mode,
            state_root=root,
            integration_execution_executor_binding_readiness_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, date, mode=mode)

    def locked(self, engine):
        values = self.helper().locked(engine)
        values["production-integration-execution-executor-binding-readiness"] = (
            engine.store.load_artifact(
                "production-integration-execution-executor-binding-readiness"
            )["content_digest"]
        )
        return values

    def data(self, root, date=DATE, mode="synthetic"):
        return RunEngine(root, date, mode=mode).store.load_artifact(
            "production-integration-execution-executor-binding-preflight"
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
            (data["real_integration_steps_enabled"], data["real_integration_steps_executed"]),
            (0, 0),
        )
        self.assertTrue(all(item["enabled"] is False for item in data["execution_steps"]))

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
        src = self.fixture("synthetic-executor-binding-preflight-qualified")
        policy = json.loads((src / "executor-binding-preflight-policy.json").read_text())
        manifest = json.loads((src / "executor-binding-preflight-manifest.json").read_text())
        record = json.loads((src / "executor-binding-preflight-record.json").read_text())
        descriptor = json.loads((src / "synthetic-binding-plan-descriptor.json").read_text())

        gate = ProductionIntegrationExecutionExecutorBindingPreflight(
            engine.store, engine.edition_date, engine.mode, root
        )
        context = gate._context(engine.store.load_run())
        bound = context["bound_upstream_identity"]

        descriptor["bound_synthetic_executor_descriptor_id"] = bound[
            "synthetic_executor_descriptor_id"
        ]
        descriptor["bound_synthetic_executor_descriptor_digest"] = bound[
            "synthetic_executor_descriptor_digest"
        ]
        if mutate_descriptor:
            mutate_descriptor(descriptor)
        descriptor_body = deepcopy(descriptor)
        descriptor_body.pop("descriptor_id", None)
        descriptor["descriptor_id"] = digest(descriptor_body)
        descriptor_binding = {
            "synthetic_binding_plan_descriptor_id": descriptor["descriptor_id"],
            "synthetic_binding_plan_descriptor_digest": digest(descriptor),
        }

        manifest["executor_binding_readiness_binding"] = {
            "binding_mode": "exact_locked_executor_binding_readiness_artifact",
            "executor_binding_readiness_artifact_digest": bound[
                "executor_binding_readiness_artifact_digest"
            ],
            "executor_binding_readiness_id": bound["executor_binding_readiness_id"],
            "executor_binding_readiness_policy_id": bound[
                "executor_binding_readiness_policy_id"
            ],
            "executor_binding_readiness_policy_digest": bound[
                "executor_binding_readiness_policy_digest"
            ],
            "executor_binding_readiness_manifest_id": bound[
                "executor_binding_readiness_manifest_id"
            ],
            "executor_binding_readiness_manifest_digest": bound[
                "executor_binding_readiness_manifest_digest"
            ],
            "separate_executor_binding_readiness_id": bound[
                "separate_executor_binding_readiness_id"
            ],
            "separate_executor_binding_readiness_digest": bound[
                "separate_executor_binding_readiness_digest"
            ],
            "synthetic_executor_descriptor_id": bound["synthetic_executor_descriptor_id"],
            "synthetic_executor_descriptor_digest": bound[
                "synthetic_executor_descriptor_digest"
            ],
            "executor_binding_provenance_validation_ids": bound[
                "executor_binding_provenance_validation_ids"
            ],
            "executor_binding_provenance_validation_digests": bound[
                "executor_binding_provenance_validation_digests"
            ],
            "executor_binding_provenance_validation_set_digest": bound[
                "executor_binding_provenance_validation_set_digest"
            ],
            "canonical_chain_digest": bound["canonical_chain_digest"],
            "iteration20_semantic_identity_digest": bound[
                "iteration20_semantic_identity_digest"
            ],
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
        }
        manifest["binding_plan_descriptor_binding"] = {
            "binding_mode": "exact_non_live_synthetic_binding_plan_descriptor",
            **descriptor_binding,
        }

        record.update(
            {
                "executor_binding_readiness_artifact_digest": bound[
                    "executor_binding_readiness_artifact_digest"
                ],
                "executor_binding_readiness_id": bound["executor_binding_readiness_id"],
                "executor_binding_readiness_policy_id": bound[
                    "executor_binding_readiness_policy_id"
                ],
                "executor_binding_readiness_policy_digest": bound[
                    "executor_binding_readiness_policy_digest"
                ],
                "executor_binding_readiness_manifest_id": bound[
                    "executor_binding_readiness_manifest_id"
                ],
                "executor_binding_readiness_manifest_digest": bound[
                    "executor_binding_readiness_manifest_digest"
                ],
                "separate_executor_binding_readiness_id": bound[
                    "separate_executor_binding_readiness_id"
                ],
                "separate_executor_binding_readiness_digest": bound[
                    "separate_executor_binding_readiness_digest"
                ],
                "synthetic_executor_descriptor_id": bound[
                    "synthetic_executor_descriptor_id"
                ],
                "synthetic_executor_descriptor_digest": bound[
                    "synthetic_executor_descriptor_digest"
                ],
                "executor_binding_provenance_validation_set_digest": bound[
                    "executor_binding_provenance_validation_set_digest"
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
        record_body.pop("preflight_record_id", None)
        record["preflight_record_id"] = digest(record_body)

        (root / "executor-binding-preflight-policy.json").write_text(json.dumps(policy))
        (root / "executor-binding-preflight-manifest.json").write_text(json.dumps(manifest))
        if include_record:
            (root / "executor-binding-preflight-record.json").write_text(json.dumps(record))
        if include_descriptor:
            (root / "synthetic-binding-plan-descriptor.json").write_text(
                json.dumps(descriptor)
            )
        return root

    def clone_root(self, source, destination):
        shutil.copytree(source, destination, dirs_exist_ok=True)

    def test_current_repository_stays_blocked_deterministic_and_zero_rework(self):
        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_executor_binding_readiness(td)
            locked = self.locked(engine)
            source = engine.store.load_artifact(
                "production-integration-execution-executor-binding-readiness"
            )["content_digest"]
            first = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_preflight_only=True,
            )
            data1 = self.data(td)
            first_digest = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-preflight"
            )["content_digest"]
            second = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_preflight_only=True,
            )
            data2 = self.data(td)
            second_digest = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-preflight"
            )["content_digest"]
            self.assertEqual(data1["classification"], "blocked")
            self.assertEqual(
                data1["classification_reason_codes"][0],
                "ITERATION20_EXECUTOR_BINDING_READINESS_BLOCKED",
            )
            self.assertEqual(data1["executor_binding_preflight_id"], data2["executor_binding_preflight_id"])
            self.assertEqual(first_digest, second_digest)
            self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
            self.assertEqual(
                RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-executor-binding-readiness"
                )["content_digest"],
                source,
            )
            for key, value in counts.items():
                self.assertEqual(first["stage_executions"].get(key), value)
                self.assertEqual(second["stage_executions"].get(key), value)
            self.safe(data1)

    def test_executor_binding_ready_requires_separate_preflight_record_and_binding_plan(self):
        with tempfile.TemporaryDirectory() as base:
            counts, engine = self.make_executor_binding_readiness(base, ready=True)
            locked = self.locked(engine)
            for missing in ("record", "descriptor"):
                with self.subTest(missing=missing), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    fixture = self.write_fixture(
                        Path(td) / "fixture",
                        e,
                        include_record=missing != "record",
                        include_descriptor=missing != "descriptor",
                    )
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_executor_binding_preflight_fixture_root=fixture,
                        integration_execution_executor_binding_preflight_only=True,
                    )
                    data = self.data(td)
                    self.assertEqual(data["classification"], "blocked")
                    expected = (
                        "EXECUTOR_BINDING_PREFLIGHT_RECORD_MISSING"
                        if missing == "record"
                        else "SYNTHETIC_BINDING_PLAN_DESCRIPTOR_MISSING"
                    )
                    self.assertEqual(data["classification_reason_codes"][0], expected)
                    self.safe(data)

            with tempfile.TemporaryDirectory() as td:
                self.clone_root(base, td)
                e = RunEngine(td, self.DATE)
                fixture = self.write_fixture(Path(td) / "fixture", e)
                first = start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_preflight_fixture_root=fixture,
                    integration_execution_executor_binding_preflight_only=True,
                )
                data = self.data(td)
                self.assertEqual(data["classification"], "executor_binding_preflight_qualified")
                self.assertEqual(
                    data["classification_reason_codes"],
                    ["SYNTHETIC_EXECUTOR_BINDING_PREFLIGHT_QUALIFIED"],
                )
                self.assertEqual(data["executor_binding_readiness_classification"], "executor_binding_ready")
                self.assertTrue(data["separate_executor_binding_preflight_id"].startswith("sha256:"))
                self.assertTrue(data["synthetic_binding_plan_descriptor_id"].startswith("sha256:"))
                self.assertEqual(len(data["executor_binding_preflight_provenance_validation_ids"]), 10)
                self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
                for key, value in counts.items():
                    self.assertEqual(first["stage_executions"].get(key), value)
                digest1 = RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-executor-binding-preflight"
                )["content_digest"]
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_preflight_fixture_root=fixture,
                    integration_execution_executor_binding_preflight_only=True,
                )
                digest2 = RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-executor-binding-preflight"
                )["content_digest"]
                self.assertEqual(digest1, digest2)
                self.safe(data)

    def test_fail_closed_iteration20_identity_and_provenance_substitution(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_readiness(base, ready=True)

            def expect_failure(mutator):
                with tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    mutator(engine)
                    with self.assertRaises(IntegrationExecutionExecutorBindingPreflightError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_preflight_fixture_root=(
                                self.write_fixture(Path(td) / "fixture", engine)
                            ),
                            integration_execution_executor_binding_preflight_only=True,
                        )

            def mutate_artifact(engine, fn):
                artifact = engine.store.load_artifact(
                    "production-integration-execution-executor-binding-readiness"
                )
                fn(artifact["data"])
                artifact["content_digest"] = semantic_digest(artifact)
                engine.store._atomic_write(
                    engine.store.artifact_path(
                        "production-integration-execution-executor-binding-readiness"
                    ),
                    artifact,
                )

            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__("executor_binding_readiness_id", "sha256:" + "0" * 64)
            ))
            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__("executor_binding_readiness_policy_id", "changed")
            ))
            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__("executor_binding_readiness_manifest_id", "changed")
            ))
            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__("separate_executor_binding_readiness_id", "sha256:" + "1" * 64)
            ))
            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__("synthetic_executor_descriptor_id", "sha256:" + "2" * 64)
            ))
            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__(
                    "executor_binding_provenance_validation_ids",
                    list(reversed(d["executor_binding_provenance_validation_ids"])),
                )
            ))
            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__(
                    "executor_binding_provenance_validation_ids",
                    [d["executor_binding_provenance_validation_ids"][0]] * 10,
                )
            ))
            expect_failure(lambda e: mutate_artifact(
                e, lambda d: d.__setitem__(
                    "executor_binding_provenance_validation_digests",
                    ["sha256:" + "3" * 64] + d["executor_binding_provenance_validation_digests"][1:],
                )
            ))

    def test_fail_closed_iteration21_versions_plan_capabilities_and_authority(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_readiness(base, ready=True)

            fixture_cases = {
                "schema": dict(mutate_policy=lambda p: p.update({"schema_version": "2.0.0"})),
                "policy-version": dict(
                    mutate_policy=lambda p: p.update({"executor_binding_preflight_policy_version": "2.0.0"})
                ),
                "policy-id": dict(mutate_policy=lambda p: p.update({"policy_id": "changed"})),
                "manifest-id": dict(mutate_manifest=lambda m: m.update({"manifest_id": "changed"})),
                "record-version": dict(mutate_record=lambda x: x.update({"record_version": "2.0.0"})),
                "descriptor-version": dict(mutate_descriptor=lambda x: x.update({"descriptor_version": "2.0.0"})),
                "real-endpoint": dict(mutate_descriptor=lambda x: x.update({"external_endpoint": "https://example.invalid"})),
                "invocation": dict(mutate_descriptor=lambda x: x.update({"invocation_capability": True})),
                "binding-capability": dict(mutate_descriptor=lambda x: x.update({"real_executor_binding_capability": True})),
                "command": dict(mutate_descriptor=lambda x: x.update({"executable_command": "echo unsafe"})),
                "step": dict(mutate_descriptor=lambda x: x.update({"executable_steps": ["unsafe"]})),
                "paid": dict(mutate_descriptor=lambda x: x.update({"paid_dependency_required": True})),
                "authority": dict(mutate_record=lambda x: x.update({"grants_production_authority": True})),
            }
            for name, kwargs in fixture_cases.items():
                with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    fixture = self.write_fixture(Path(td) / "fixture", engine, **kwargs)
                    with self.assertRaises(IntegrationExecutionExecutorBindingPreflightError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_preflight_fixture_root=fixture,
                            integration_execution_executor_binding_preflight_only=True,
                        )

            with tempfile.TemporaryDirectory() as td:
                self.clone_root(base, td)
                engine = RunEngine(td, self.DATE)
                artifact = engine.store.load_artifact(
                    "production-integration-execution-executor-binding-readiness"
                )
                artifact["data"]["production_action_authorized"] = True
                artifact["content_digest"] = semantic_digest(artifact)
                engine.store._atomic_write(
                    engine.store.artifact_path(
                        "production-integration-execution-executor-binding-readiness"
                    ),
                    artifact,
                )
                with self.assertRaises(IntegrationExecutionExecutorBindingPreflightError):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_executor_binding_preflight_only=True,
                    )

    def recovery(self, source_root, boundary):
        temp = tempfile.TemporaryDirectory()
        root = temp.name
        self.clone_root(source_root, root)
        engine = RunEngine(root, self.DATE)
        counts = deepcopy(engine.store.load_run()["stage_executions"])
        locked = self.locked(engine)
        source_digest = engine.store.load_artifact(
            "production-integration-execution-executor-binding-readiness"
        )["content_digest"]
        fixture = self.write_fixture(Path(root) / "recovery", engine)
        failing = RunEngine(
            root,
            self.DATE,
            failure_injection=FailureInjection(
                "Complete", "synthetic_i21_failure", boundary
            ),
            integration_execution_executor_binding_preflight_fixture_root=fixture,
            integration_execution_executor_binding_preflight_only=True,
        )
        with self.assertRaises(IntegrationExecutionExecutorBindingPreflightBoundaryFailure):
            failing.run()
        start_daily_brief(
            self.DATE,
            state_root=root,
            integration_execution_executor_binding_preflight_fixture_root=fixture,
            integration_execution_executor_binding_preflight_only=True,
        )
        fresh = RunEngine(root, self.DATE)
        self.assertEqual(self.locked(fresh), locked)
        self.assertEqual(
            fresh.store.load_artifact(
                "production-integration-execution-executor-binding-readiness"
            )["content_digest"],
            source_digest,
        )
        for key, value in counts.items():
            self.assertEqual(fresh.store.load_run()["stage_executions"].get(key), value)
        self.assertEqual(
            fresh.store.read_json(
                fresh.store.run_dir / "executor-binding-preflight-incident.json"
            )["result"],
            "recovered",
        )
        return temp, fresh

    def test_targeted_recovery_fresh_engine_no_rework(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_readiness(base, ready=True)

            temp, engine = self.recovery(base, "executor_binding_preflight:evaluation")
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-preflight-state.json"
            )
            self.assertEqual(state["attempts"]["evaluation"], 2)
            temp.cleanup()

            temp, engine = self.recovery(base, "executor_binding_preflight:validation:5")
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-preflight-state.json"
            )
            self.assertGreaterEqual(state["metrics"]["provenance_validation_reuse"], 4)
            self.assertEqual(len(state["validation_digests"]), 10)
            temp.cleanup()

            temp, engine = self.recovery(
                base, "executor_binding_preflight:final_executor_binding_preflight_artifact"
            )
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-preflight-state.json"
            )
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state["metrics"]["provenance_validation_reuse"], 10)
            temp.cleanup()

    def test_bounded_exclusive_production_fail_closed_and_schema(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_preflight_only=True,
                )
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_executor_binding_readiness_only=True,
                    integration_execution_executor_binding_preflight_only=True,
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_executor_binding_preflight_only=True,
                )

        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-executor-binding-preflight.schema.json"
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
                counts, engine = self.make_executor_binding_readiness(
                    td, date, "shadow"
                )
                locked = self.locked(engine)
                run = start_daily_brief(
                    date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_executor_binding_preflight_only=True,
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
                        data["executor_binding_preflight_id"],
                    )
                )
        self.assertEqual(outcomes[0][0], "blocked")
        self.assertEqual(outcomes[0][0:2], outcomes[1][0:2])
        self.assertEqual(outcomes[1][0:2], outcomes[2][0:2])


if __name__ == "__main__":
    unittest.main()
