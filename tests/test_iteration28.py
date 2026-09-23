from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_executor_binding_authorization_package_readiness_rehearsal import (
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure,
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError,
    ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsal,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration27


class Iteration28ExecutorBindingAuthorizationPackageReadinessRehearsalTest(unittest.TestCase):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration27.Iteration27ExecutorBindingAuthorizationPackageReadinessPreflightTest(
            methodName="test_current_repository_stays_blocked_deterministic_and_zero_rework"
        )

    def fixture(self, name):
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration28" / name

    def make_executor_binding_authorization_package_readiness_preflight(
        self, root, date=DATE, mode="synthetic", qualified=False
    ):
        h = self.helper()
        _, engine = h.make_source(root, date, mode, qualified=qualified)
        kwargs = {}
        if qualified:
            kwargs["integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root"] = (
                h.write_fixture(Path(root) / "i27-qualified", engine)
            )
        run = start_daily_brief(
            date,
            mode=mode,
            state_root=root,
            integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, date, mode=mode)

    def locked(self, engine):
        values = self.helper().locked(engine)
        values["production-integration-execution-executor-binding-authorization-package-readiness-preflight"] = (
            engine.store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
            )["content_digest"]
        )
        return values

    def data(self, root, date=DATE, mode="synthetic"):
        return RunEngine(root, date, mode=mode).store.load_artifact(
            "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
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

    def write_fixture(
        self,
        root,
        engine,
        *,
        include_record=True,
        mutate_policy=None,
        mutate_manifest=None,
        mutate_record=None,
    ):
        root.mkdir(parents=True, exist_ok=True)
        src = self.fixture("synthetic-executor-binding-authorization-package-readiness-rehearsal-complete")
        policy = json.loads((src / "executor-binding-authorization-package-readiness-rehearsal-policy.json").read_text())
        manifest = json.loads((src / "executor-binding-authorization-package-readiness-rehearsal-manifest.json").read_text())
        record = json.loads((src / "executor-binding-authorization-package-readiness-rehearsal-record.json").read_text())

        gate = ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsal(
            engine.store, engine.edition_date, engine.mode, root
        )
        context = gate._context(engine.store.load_run())
        bound = context["bound_upstream_identity"]
        manifest["executor_binding_authorization_package_readiness_preflight_binding"] = {
            "binding_mode": "exact_locked_executor_binding_authorization_package_readiness_preflight_artifact",
            "executor_binding_authorization_package_readiness_preflight_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_preflight_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_preflight_id": bound["executor_binding_authorization_package_readiness_preflight_id"],
            "executor_binding_authorization_package_readiness_preflight_policy_id": bound[
                "executor_binding_authorization_package_readiness_preflight_policy_id"
            ],
            "executor_binding_authorization_package_readiness_preflight_policy_digest": bound[
                "executor_binding_authorization_package_readiness_preflight_policy_digest"
            ],
            "executor_binding_authorization_package_readiness_preflight_manifest_id": bound[
                "executor_binding_authorization_package_readiness_preflight_manifest_id"
            ],
            "executor_binding_authorization_package_readiness_preflight_manifest_digest": bound[
                "executor_binding_authorization_package_readiness_preflight_manifest_digest"
            ],
            "separate_executor_binding_authorization_package_readiness_preflight_id": bound[
                "separate_executor_binding_authorization_package_readiness_preflight_id"
            ],
            "separate_executor_binding_authorization_package_readiness_preflight_digest": bound[
                "separate_executor_binding_authorization_package_readiness_preflight_digest"
            ],
            "synthetic_binding_plan_descriptor_id": bound[
                "synthetic_binding_plan_descriptor_id"
            ],
            "synthetic_binding_plan_descriptor_digest": bound[
                "synthetic_binding_plan_descriptor_digest"
            ],
            "executor_binding_authorization_package_readiness_preflight_evidence_ids": bound[
                "executor_binding_authorization_package_readiness_preflight_evidence_ids"
            ],
            "executor_binding_authorization_package_readiness_preflight_evidence_digests": bound[
                "executor_binding_authorization_package_readiness_preflight_evidence_digests"
            ],
            "executor_binding_authorization_package_readiness_preflight_evidence_set_digest": bound[
                "executor_binding_authorization_package_readiness_preflight_evidence_set_digest"
            ],
            "canonical_chain_digest": bound["canonical_chain_digest"],
            "iteration27_semantic_identity_digest": bound[
                "iteration27_semantic_identity_digest"
            ],
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
        }
        record.update(
            {
                "noop": True,
                "non_live": True,
                "bound_upstream_identity": deepcopy(bound),
                "executor_binding_authorization_package_readiness_preflight_artifact_digest": bound[
                    "executor_binding_authorization_package_readiness_preflight_artifact_digest"
                ],
                "executor_binding_authorization_package_readiness_preflight_id": bound[
                    "executor_binding_authorization_package_readiness_preflight_id"
                ],
                "executor_binding_authorization_package_readiness_preflight_policy_id": bound[
                    "executor_binding_authorization_package_readiness_preflight_policy_id"
                ],
                "executor_binding_authorization_package_readiness_preflight_policy_digest": bound[
                    "executor_binding_authorization_package_readiness_preflight_policy_digest"
                ],
                "executor_binding_authorization_package_readiness_preflight_manifest_id": bound[
                    "executor_binding_authorization_package_readiness_preflight_manifest_id"
                ],
                "executor_binding_authorization_package_readiness_preflight_manifest_digest": bound[
                    "executor_binding_authorization_package_readiness_preflight_manifest_digest"
                ],
                "separate_executor_binding_authorization_package_readiness_preflight_id": bound[
                    "separate_executor_binding_authorization_package_readiness_preflight_id"
                ],
                "separate_executor_binding_authorization_package_readiness_preflight_digest": bound[
                    "separate_executor_binding_authorization_package_readiness_preflight_digest"
                ],
                "synthetic_binding_plan_descriptor_id": bound[
                    "synthetic_binding_plan_descriptor_id"
                ],
                "synthetic_binding_plan_descriptor_digest": bound[
                    "synthetic_binding_plan_descriptor_digest"
                ],
                "executor_binding_authorization_package_readiness_preflight_evidence_ids": deepcopy(
                    bound["executor_binding_authorization_package_readiness_preflight_evidence_ids"]
                ),
                "executor_binding_authorization_package_readiness_preflight_evidence_digests": deepcopy(
                    bound["executor_binding_authorization_package_readiness_preflight_evidence_digests"]
                ),
                "executor_binding_authorization_package_readiness_preflight_evidence_set_digest": bound[
                    "executor_binding_authorization_package_readiness_preflight_evidence_set_digest"
                ],
                "iteration24_semantic_identity_digest": bound["iteration24_semantic_identity_digest"],
                "iteration25_semantic_identity_digest": bound["iteration25_semantic_identity_digest"],
                "iteration26_semantic_identity_digest": bound["iteration26_semantic_identity_digest"],
                "iteration27_semantic_identity_digest": bound["iteration27_semantic_identity_digest"],
                "canonical_chain_digest": bound["canonical_chain_digest"],
                "bound_upstream_identity_digest": context[
                    "bound_upstream_identity_digest"
                ],
            }
        )
        if mutate_policy:
            mutate_policy(policy)
        if mutate_manifest:
            mutate_manifest(manifest)
        if mutate_record:
            mutate_record(record)
        body = deepcopy(record)
        body.pop("rehearsal_record_id", None)
        record["rehearsal_record_id"] = digest(body)

        (root / "executor-binding-authorization-package-readiness-rehearsal-policy.json").write_text(json.dumps(policy))
        (root / "executor-binding-authorization-package-readiness-rehearsal-manifest.json").write_text(json.dumps(manifest))
        if include_record:
            (root / "executor-binding-authorization-package-readiness-rehearsal-record.json").write_text(
                json.dumps(record)
            )
        return root

    def clone_root(self, source, destination):
        shutil.copytree(source, destination, dirs_exist_ok=True)

    def snapshot_upstream(self, engine):
        result = {}
        for path in engine.store.run_dir.rglob("*.json"):
            name = path.name
            if name in {"run.json", "lease.json"}:
                continue
            if name.startswith("executor-binding-authorization-package-readiness-rehearsal"):
                continue
            if name == "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal.json":
                continue
            result[str(path.relative_to(engine.store.run_dir))] = (
                path.read_bytes(),
                path.stat().st_mtime_ns,
            )
        return result

    def test_current_repository_stays_blocked_deterministic_and_zero_rework(self):
        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_executor_binding_authorization_package_readiness_preflight(td)
            locked = self.locked(engine)
            before = self.snapshot_upstream(engine)
            source_digest = engine.store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
            )["content_digest"]
            first = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
            )
            data1 = self.data(td)
            digest1 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
            )["content_digest"]
            second = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
            )
            data2 = self.data(td)
            digest2 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
            )["content_digest"]
            self.assertEqual(data1["classification"], "blocked")
            self.assertEqual(
                data1["classification_reason_codes"][0],
                "ITERATION27_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_BLOCKED",
            )
            self.assertEqual(data1["executor_binding_authorization_package_readiness_rehearsal_id"], data2["executor_binding_authorization_package_readiness_rehearsal_id"])
            self.assertEqual(digest1, digest2)
            self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
            self.assertEqual(
                RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                )["content_digest"],
                source_digest,
            )
            self.assertEqual(before, self.snapshot_upstream(RunEngine(td, self.DATE)))
            for key, value in counts.items():
                self.assertEqual(first["stage_executions"].get(key), value)
                self.assertEqual(second["stage_executions"].get(key), value)
            self.safe(data1)

    def test_qualified_preflight_requires_separate_record_and_complete_noop_receipts(self):
        with tempfile.TemporaryDirectory() as base:
            counts, engine = self.make_executor_binding_authorization_package_readiness_preflight(base, qualified=True)
            locked = self.locked(engine)

            with tempfile.TemporaryDirectory() as td:
                self.clone_root(base, td)
                e = RunEngine(td, self.DATE)
                fixture = self.write_fixture(
                    Path(td) / "missing-record", e, include_record=False
                )
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                )
                data = self.data(td)
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(
                    data["classification_reason_codes"][0],
                    "EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_RECORD_MISSING",
                )
                self.assertEqual(data["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"], [])
                self.safe(data)

            with tempfile.TemporaryDirectory() as td:
                self.clone_root(base, td)
                e = RunEngine(td, self.DATE)
                fixture = self.write_fixture(Path(td) / "complete", e)
                run = start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                )
                data = self.data(td)
                self.assertEqual(data["classification"], "executor_binding_authorization_package_readiness_rehearsal_complete")
                self.assertEqual(
                    data["classification_reason_codes"],
                    ["SYNTHETIC_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_COMPLETE"],
                )
                self.assertEqual(
                    data["executor_binding_authorization_package_readiness_preflight_classification"],
                    "executor_binding_authorization_package_readiness_preflight_complete",
                )
                self.assertEqual(len(data["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"]), 10)
                self.assertEqual(len(set(data["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"])), 10)
                for position in range(1, 11):
                    receipt = e.store.read_json(
                        e.store.run_dir
                        / f"executor-binding-authorization-package-readiness-rehearsal-receipt-{position:02d}.json"
                    )
                    self.assertTrue(receipt["noop_verified"])
                    self.assertTrue(receipt["side_effect_free_verified"])
                    for key in (
                        "real_executor_binding_performed",
                        "real_executor_invocation_performed",
                        "credential_use_performed",
                        "real_target_contact_performed",
                        "network_side_effect_performed",
                        "production_write_performed",
                        "rollback_execution_performed",
                        "cutover_execution_performed",
                        "decommission_execution_performed",
                        "publication_execution_performed",
                        "external_mutation_performed",
                        "executable_step",
                    ):
                        self.assertFalse(receipt[key])
                    self.assertIsNone(receipt["executable_command"])
                self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
                for key, value in counts.items():
                    self.assertEqual(run["stage_executions"].get(key), value)
                artifact1 = e.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
                )["content_digest"]
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                )
                artifact2 = e.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
                )["content_digest"]
                self.assertEqual(artifact1, artifact2)
                self.safe(data)

    def test_fail_closed_iteration27_identity_and_provenance_substitution(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_preflight(base, qualified=True)

            def mutate_artifact(engine, fn):
                artifact = engine.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                )
                fn(artifact["data"])
                artifact["content_digest"] = semantic_digest(artifact)
                engine.store._atomic_write(
                    engine.store.artifact_path(
                        "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                    ),
                    artifact,
                )

            cases = [
                lambda d: d.__setitem__("executor_binding_authorization_package_readiness_preflight_id", "sha256:" + "0" * 64),
                lambda d: d.__setitem__("executor_binding_authorization_package_readiness_preflight_policy_id", "changed"),
                lambda d: d.__setitem__("executor_binding_authorization_package_readiness_preflight_manifest_id", "changed"),
                lambda d: d.__setitem__("separate_executor_binding_authorization_package_readiness_preflight_id", "sha256:" + "1" * 64),
                lambda d: d.__setitem__("executor_binding_authorization_package_readiness_id", "sha256:" + "2" * 64),
                lambda d: d.__setitem__("executor_binding_authorization_package_id", "sha256:" + "4" * 64),
                lambda d: d.__setitem__("executor_binding_authorization_decision_id", "sha256:" + "5" * 64),
                lambda d: d.__setitem__("iteration24_semantic_identity_digest", "sha256:" + "6" * 64),
                lambda d: d.__setitem__("iteration25_semantic_identity_digest", "sha256:" + "7" * 64),
                lambda d: d.__setitem__("iteration26_semantic_identity_digest", "sha256:" + "8" * 64),
                lambda d: d.__setitem__(
                    "executor_binding_authorization_package_readiness_preflight_evidence_ids",
                    list(reversed(d["executor_binding_authorization_package_readiness_preflight_evidence_ids"])),
                ),
                lambda d: d.__setitem__(
                    "executor_binding_authorization_package_readiness_preflight_evidence_ids",
                    [d["executor_binding_authorization_package_readiness_preflight_evidence_ids"][0]] * 10,
                ),
                lambda d: d.__setitem__(
                    "executor_binding_authorization_package_readiness_preflight_evidence_digests",
                    ["sha256:" + "3" * 64]
                    + d["executor_binding_authorization_package_readiness_preflight_evidence_digests"][1:],
                ),
            ]
            for idx, fn in enumerate(cases):
                with self.subTest(case=idx), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    mutate_artifact(engine, fn)
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=(
                                self.write_fixture(Path(td) / "fixture", engine)
                            ),
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                        )

    def test_fail_closed_iteration28_versions_source_capabilities_authority_and_cost(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_preflight(base, qualified=True)
            fixture_cases = {
                "schema": dict(mutate_policy=lambda p: p.update({"schema_version": "2.0.0"})),
                "policy-version": dict(
                    mutate_policy=lambda p: p.update(
                        {"executor_binding_authorization_package_readiness_rehearsal_policy_version": "2.0.0"}
                    )
                ),
                "policy-id": dict(mutate_policy=lambda p: p.update({"policy_id": "changed"})),
                "manifest-id": dict(mutate_manifest=lambda m: m.update({"manifest_id": "changed"})),
                "record-version": dict(mutate_record=lambda r: r.update({"record_version": "2.0.0"})),
                "authority": dict(mutate_record=lambda r: r.update({"grants_production_authority": True})),
                "credential-authority": dict(mutate_record=lambda r: r.update({"grants_credential_use_authority": True})),
                "target-authority": dict(mutate_record=lambda r: r.update({"grants_real_target_contact_authority": True})),
                "rollback-authority": dict(mutate_record=lambda r: r.update({"grants_rollback_execution_authority": True})),
                "cost": dict(mutate_record=lambda r: r.update({"zero_incremental_cost_approved": False})),
            }
            for name, kwargs in fixture_cases.items():
                with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    fixture = self.write_fixture(Path(td) / "fixture", engine, **kwargs)
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=fixture,
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                        )

            source_cases = {
                "endpoint": lambda d: d.__setitem__("external_endpoint", "https://example.invalid"),
                "invocation": lambda d: d.__setitem__("invocation_capability", True),
                "binding": lambda d: d.__setitem__("real_executor_binding_capability", True),
                "command": lambda d: d.__setitem__("executable_command", "echo unsafe"),
                "step": lambda d: d.__setitem__("executable_step", True),
                "credential": lambda d: d.__setitem__("credential_reference", "secret"),
                "target": lambda d: d.__setitem__("deployment_target", "prod"),
                "paid": lambda d: d.__setitem__("incremental_paid_dependency_added", True),
                "mutation": lambda d: d.__setitem__("external_mutation_performed", True),
                "authority-flag": lambda d: d.__setitem__("production_action_authorized", True),
            }
            for name, mut in source_cases.items():
                with self.subTest(source=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    artifact = engine.store.load_artifact(
                        "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                    )
                    mut(artifact["data"])
                    artifact["content_digest"] = semantic_digest(artifact)
                    engine.store._atomic_write(
                        engine.store.artifact_path(
                            "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                        ),
                        artifact,
                    )
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                        )

    def test_fail_closed_iteration27_evidence_missing_corrupted_reordered_duplicated_substituted(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_preflight(base, qualified=True)

            def expect_source_failure(mutator):
                with tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    mutator(e)
                    with self.assertRaises(
                        IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                        )

            def corrupt(e):
                p = e.store.run_dir / "executor-binding-authorization-package-readiness-preflight-evidence-01.json"
                r = e.store.read_json(p)
                r["position"] = 2
                e.store._atomic_write(p, r)
            expect_source_failure(corrupt)

            def missing(e):
                (e.store.run_dir / "executor-binding-authorization-package-readiness-preflight-evidence-02.json").unlink()
            expect_source_failure(missing)

            def duplicate(e):
                p1 = e.store.run_dir / "executor-binding-authorization-package-readiness-preflight-evidence-01.json"
                p2 = e.store.run_dir / "executor-binding-authorization-package-readiness-preflight-evidence-02.json"
                p2.write_bytes(p1.read_bytes())
            expect_source_failure(duplicate)

            def substitute(e):
                p = e.store.run_dir / "executor-binding-authorization-package-readiness-preflight-evidence-03.json"
                r = e.store.read_json(p)
                r["receipt_id"] = "sha256:" + "a" * 64
                e.store._atomic_write(p, r)
            expect_source_failure(substitute)

            def reorder_inventory(e):
                a = e.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                )
                ids = a["data"]["executor_binding_authorization_package_readiness_preflight_evidence_ids"]
                ids[0], ids[1] = ids[1], ids[0]
                a["content_digest"] = semantic_digest(a)
                e.store._atomic_write(
                    e.store.artifact_path(
                        "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
                    ),
                    a,
                )
            expect_source_failure(reorder_inventory)

    def test_fail_closed_reordered_duplicated_missing_substituted_corrupted_receipts(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_preflight(base, qualified=True)
            engine = RunEngine(base, self.DATE)
            fixture = self.write_fixture(Path(base) / "fixture", engine)
            start_daily_brief(
                self.DATE,
                state_root=base,
                integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=fixture,
                integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
            )

            def expect_receipt_failure(mutator):
                with tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    mutator(e)
                    with self.assertRaises(
                        (
                            IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError,
                            IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure,
                        )
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=Path(td) / "fixture",
                            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                        )

            def mutate_final(e, fn):
                artifact = e.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
                )
                fn(artifact["data"])
                artifact["content_digest"] = semantic_digest(artifact)
                e.store._atomic_write(
                    e.store.artifact_path(
                        "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
                    ),
                    artifact,
                )

            expect_receipt_failure(
                lambda e: mutate_final(
                    e,
                    lambda d: d.__setitem__(
                        "executor_binding_authorization_package_readiness_rehearsal_receipt_ids",
                        list(reversed(d["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"])),
                    ),
                )
            )
            expect_receipt_failure(
                lambda e: mutate_final(
                    e,
                    lambda d: d.__setitem__(
                        "executor_binding_authorization_package_readiness_rehearsal_receipt_ids",
                        [d["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"][0]] * 10,
                    ),
                )
            )
            expect_receipt_failure(
                lambda e: mutate_final(
                    e,
                    lambda d: d.__setitem__(
                        "executor_binding_authorization_package_readiness_rehearsal_receipt_ids",
                        d["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"][:-1],
                    ),
                )
            )

            def corrupt_receipt(e):
                path = e.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-receipt-05.json"
                r = e.store.read_json(path)
                r["source_executor_binding_authorization_package_readiness_preflight_evidence_id"] = "sha256:" + "9" * 64
                e.store._atomic_write(path, r)
            expect_receipt_failure(corrupt_receipt)

            def unsupported_receipt(e):
                path = e.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-receipt-05.json"
                r = e.store.read_json(path)
                r["receipt_version"] = "2.0.0"
                e.store._atomic_write(path, r)
            expect_receipt_failure(unsupported_receipt)

            def missing_receipt(e):
                (e.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-receipt-05.json").unlink()
            expect_receipt_failure(missing_receipt)

    def recovery(self, source_root, boundary):
        temp = tempfile.TemporaryDirectory()
        root = temp.name
        self.clone_root(source_root, root)
        engine = RunEngine(root, self.DATE)
        counts = deepcopy(engine.store.load_run()["stage_executions"])
        locked = self.locked(engine)
        upstream = self.snapshot_upstream(engine)
        source_digest = engine.store.load_artifact(
            "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
        )["content_digest"]
        fixture = self.write_fixture(Path(root) / "recovery", engine)
        failing = RunEngine(
            root,
            self.DATE,
            failure_injection=FailureInjection(
                "Complete", "synthetic_i28_failure", boundary
            ),
            integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=fixture,
            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
        )
        with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure):
            failing.run()
        durable = {
            p.name: (p.read_bytes(), p.stat().st_mtime_ns)
            for p in engine.store.run_dir.glob(
                "executor-binding-authorization-package-readiness-rehearsal-receipt-*.json"
            )
        }
        start_daily_brief(
            self.DATE,
            state_root=root,
            integration_execution_executor_binding_authorization_package_readiness_rehearsal_fixture_root=fixture,
            integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
        )
        fresh = RunEngine(root, self.DATE)
        self.assertEqual(self.locked(fresh), locked)
        self.assertEqual(
            fresh.store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
            )["content_digest"],
            source_digest,
        )
        for key, value in counts.items():
            self.assertEqual(fresh.store.load_run()["stage_executions"].get(key), value)
        self.assertEqual(upstream, self.snapshot_upstream(fresh))
        for name, value in durable.items():
            p = fresh.store.run_dir / name
            self.assertEqual(value, (p.read_bytes(), p.stat().st_mtime_ns))
        self.assertEqual(
            fresh.store.read_json(
                fresh.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-incident.json"
            )["result"],
            "recovered",
        )
        return temp, fresh

    def test_targeted_recovery_fresh_engine_no_rework(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_preflight(base, qualified=True)

            temp, engine = self.recovery(base, "executor_binding_authorization_package_readiness_rehearsal:evaluation")
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-state.json"
            )
            self.assertEqual(state["attempts"]["evaluation"], 2)
            temp.cleanup()

            temp, engine = self.recovery(base, "executor_binding_authorization_package_readiness_rehearsal:validation:5")
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-state.json"
            )
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 4)
            self.assertEqual(len(state["receipt_digests"]), 10)
            temp.cleanup()

            temp, engine = self.recovery(
                base, "executor_binding_authorization_package_readiness_rehearsal:final_executor_binding_authorization_package_readiness_rehearsal_artifact"
            )
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-state.json"
            )
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 10)
            temp.cleanup()

    def test_bounded_exclusive_production_fail_closed_and_schema(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                )
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
                )
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal.schema.json"
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
        complete_branches = [
            branch for branch in schema.get("allOf", [])
            if "separate_executor_binding_authorization_package_readiness_rehearsal_id"
            in branch.get("then", {}).get("required", [])
        ]
        self.assertEqual(len(complete_branches), 1)
        props = complete_branches[0]["then"]["properties"]
        self.assertEqual(
            props["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"]["minItems"],
            10,
        )
        self.assertEqual(
            props["executor_binding_authorization_package_readiness_rehearsal_receipt_ids"]["maxItems"],
            10,
        )

    def test_three_run_exit_gate_is_blocked_stable_and_independent(self):
        outcomes = []
        for date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                counts, engine = self.make_executor_binding_authorization_package_readiness_preflight(
                    td, date, "shadow"
                )
                locked = self.locked(engine)
                run = start_daily_brief(
                    date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_rehearsal_only=True,
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
                        data["executor_binding_authorization_package_readiness_rehearsal_id"],
                    )
                )
        self.assertEqual(outcomes[0][0], "blocked")
        self.assertEqual(outcomes[0][0:2], outcomes[1][0:2])
        self.assertEqual(outcomes[1][0:2], outcomes[2][0:2])


if __name__ == "__main__":
    unittest.main()
