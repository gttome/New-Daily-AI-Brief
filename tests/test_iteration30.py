from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_executor_binding_authorization_package_readiness_authorization_decision import (
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionBoundaryFailure,
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError,
    ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecision,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration29


class Iteration24ExecutorBindingAuthorizationDecisionTest(unittest.TestCase):
    DATE = "2026-09-22"

    def emit(self, kind, data):
        destination = os.environ.get("NDAIB_ITERATION30_EVIDENCE_OUT")
        if destination:
            with open(destination, "a", encoding="utf-8") as stream:
                stream.write(json.dumps({"kind": kind, **data}, sort_keys=True) + "\n")

    def snapshot(self, engine):
        return {str(p.relative_to(engine.store.run_dir)): (p.read_bytes(), p.stat().st_mtime_ns)
                for p in engine.store.run_dir.rglob("*.json")
                if p.name not in {"run.json", "lease.json"}
                and not p.name.startswith("executor-binding-authorization-package-readiness-authorization-decision")
                and p.name != "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision.json"}

    def helper(self):
        return test_iteration29.Iteration23ExecutorBindingAuthorizationReviewTest(
            methodName="test_current_repository_stays_blocked_deterministic_and_zero_rework"
        )

    def fixture(self, name):
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration30" / name

    def make_executor_binding_authorization_package_readiness_authorization_review(
        self, root, date=DATE, mode="synthetic", qualified=False
    ):
        h = self.helper()
        _, engine = h.make_executor_binding_authorization_package_readiness_rehearsal(root, date, mode, qualified=qualified)
        kwargs = {}
        if qualified:
            kwargs["integration_execution_executor_binding_authorization_package_readiness_authorization_review_fixture_root"] = (
                h.write_fixture(Path(root) / "i29-qualified", engine)
            )
        run = start_daily_brief(
            date,
            mode=mode,
            state_root=root,
            integration_execution_executor_binding_authorization_package_readiness_authorization_review_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, date, mode=mode)

    def locked(self, engine):
        values = self.helper().locked(engine)
        values["production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"] = (
            engine.store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
            )["content_digest"]
        )
        return values

    def data(self, root, date=DATE, mode="synthetic"):
        return RunEngine(root, date, mode=mode).store.load_artifact(
            "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
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
        src = self.fixture("synthetic-executor-binding-authorization-package-readiness-authorization-decision-complete")
        policy = json.loads((src / "executor-binding-authorization-package-readiness-authorization-decision-policy.json").read_text())
        manifest = json.loads((src / "executor-binding-authorization-package-readiness-authorization-decision-manifest.json").read_text())
        record = json.loads((src / "executor-binding-authorization-package-readiness-authorization-decision-record.json").read_text())

        gate = ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecision(
            engine.store, engine.edition_date, engine.mode, root
        )
        context = gate._context(engine.store.load_run())
        bound = context["bound_upstream_identity"]
        manifest["executor_binding_authorization_package_readiness_authorization_review_binding"] = {
            "binding_mode": "exact_locked_executor_binding_authorization_package_readiness_authorization_review_artifact",
            "executor_binding_authorization_package_readiness_authorization_review_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_authorization_review_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_authorization_review_id": bound["executor_binding_authorization_package_readiness_authorization_review_id"],
            "executor_binding_authorization_package_readiness_authorization_review_policy_id": bound[
                "executor_binding_authorization_package_readiness_authorization_review_policy_id"
            ],
            "executor_binding_authorization_package_readiness_authorization_review_policy_digest": bound[
                "executor_binding_authorization_package_readiness_authorization_review_policy_digest"
            ],
            "executor_binding_authorization_package_readiness_authorization_review_manifest_id": bound[
                "executor_binding_authorization_package_readiness_authorization_review_manifest_id"
            ],
            "executor_binding_authorization_package_readiness_authorization_review_manifest_digest": bound[
                "executor_binding_authorization_package_readiness_authorization_review_manifest_digest"
            ],
            "separate_executor_binding_authorization_package_readiness_authorization_review_id": bound[
                "separate_executor_binding_authorization_package_readiness_authorization_review_id"
            ],
            "separate_executor_binding_authorization_package_readiness_authorization_review_digest": bound[
                "separate_executor_binding_authorization_package_readiness_authorization_review_digest"
            ],
            "synthetic_binding_plan_descriptor_id": bound[
                "synthetic_binding_plan_descriptor_id"
            ],
            "synthetic_binding_plan_descriptor_digest": bound[
                "synthetic_binding_plan_descriptor_digest"
            ],
            "executor_binding_authorization_package_readiness_authorization_review_evidence_ids": bound[
                "executor_binding_authorization_package_readiness_authorization_review_evidence_ids"
            ],
            "executor_binding_authorization_package_readiness_authorization_review_evidence_digests": bound[
                "executor_binding_authorization_package_readiness_authorization_review_evidence_digests"
            ],
            "executor_binding_authorization_package_readiness_authorization_review_evidence_set_digest": bound[
                "executor_binding_authorization_package_readiness_authorization_review_evidence_set_digest"
            ],
            "canonical_chain_digest": bound["canonical_chain_digest"],
            "iteration29_semantic_identity_digest": bound[
                "iteration29_semantic_identity_digest"
            ],
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
        }
        record["executor_binding_authorization_package_readiness_authorization_review_evidence_ids"] = bound["executor_binding_authorization_package_readiness_authorization_review_evidence_ids"]
        record["executor_binding_authorization_package_readiness_authorization_review_evidence_digests"] = bound["executor_binding_authorization_package_readiness_authorization_review_evidence_digests"]
        record.update(
            {
                "executor_binding_authorization_package_readiness_authorization_review_artifact_digest": bound[
                    "executor_binding_authorization_package_readiness_authorization_review_artifact_digest"
                ],
                "executor_binding_authorization_package_readiness_authorization_review_id": bound[
                    "executor_binding_authorization_package_readiness_authorization_review_id"
                ],
                "executor_binding_authorization_package_readiness_authorization_review_policy_id": bound[
                    "executor_binding_authorization_package_readiness_authorization_review_policy_id"
                ],
                "executor_binding_authorization_package_readiness_authorization_review_policy_digest": bound[
                    "executor_binding_authorization_package_readiness_authorization_review_policy_digest"
                ],
                "executor_binding_authorization_package_readiness_authorization_review_manifest_id": bound[
                    "executor_binding_authorization_package_readiness_authorization_review_manifest_id"
                ],
                "executor_binding_authorization_package_readiness_authorization_review_manifest_digest": bound[
                    "executor_binding_authorization_package_readiness_authorization_review_manifest_digest"
                ],
                "separate_executor_binding_authorization_package_readiness_authorization_review_id": bound[
                    "separate_executor_binding_authorization_package_readiness_authorization_review_id"
                ],
                "separate_executor_binding_authorization_package_readiness_authorization_review_digest": bound[
                    "separate_executor_binding_authorization_package_readiness_authorization_review_digest"
                ],
                "synthetic_binding_plan_descriptor_id": bound[
                    "synthetic_binding_plan_descriptor_id"
                ],
                "synthetic_binding_plan_descriptor_digest": bound[
                    "synthetic_binding_plan_descriptor_digest"
                ],
                "executor_binding_authorization_package_readiness_authorization_review_evidence_set_digest": bound[
                    "executor_binding_authorization_package_readiness_authorization_review_evidence_set_digest"
                ],
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
        body.pop("authorization_decision_record_id", None)
        record["authorization_decision_record_id"] = digest(body)

        (root / "executor-binding-authorization-package-readiness-authorization-decision-policy.json").write_text(json.dumps(policy))
        (root / "executor-binding-authorization-package-readiness-authorization-decision-manifest.json").write_text(json.dumps(manifest))
        if include_record:
            (root / "executor-binding-authorization-package-readiness-authorization-decision-record.json").write_text(
                json.dumps(record)
            )
        return root

    def clone_root(self, source, destination):
        shutil.copytree(source, destination, dirs_exist_ok=True)

    def test_current_repository_stays_blocked_deterministic_and_zero_rework(self):
        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_executor_binding_authorization_package_readiness_authorization_review(td)
            locked = self.locked(engine)
            source_digest = engine.store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
            )["content_digest"]
            first = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
            )
            data1 = self.data(td)
            digest1 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
            )["content_digest"]
            second = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
            )
            data2 = self.data(td)
            digest2 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
            )["content_digest"]
            self.assertEqual(data1["classification"], "blocked")
            self.assertEqual(
                data1["classification_reason_codes"][0],
                "ITERATION29_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_AUTHORIZATION_REVIEW_BLOCKED",
            )
            self.assertEqual(data1["executor_binding_authorization_package_readiness_authorization_decision_id"], data2["executor_binding_authorization_package_readiness_authorization_decision_id"])
            self.assertEqual(digest1, digest2)
            self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
            self.assertEqual(
                RunEngine(td, self.DATE).store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
                )["content_digest"],
                source_digest,
            )
            for key, value in counts.items():
                self.assertEqual(first["stage_executions"].get(key), value)
                self.assertEqual(second["stage_executions"].get(key), value)
            self.safe(data1)

    def test_complete_review_requires_separate_record_and_complete_decision_evidence(self):
        with tempfile.TemporaryDirectory() as base:
            counts, engine = self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)
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
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                )
                data = self.data(td)
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(
                    data["classification_reason_codes"][0],
                    "EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_AUTHORIZATION_DECISION_RECORD_MISSING",
                )
                self.assertEqual(data["executor_binding_authorization_package_readiness_authorization_decision_evidence_ids"], [])
                self.safe(data)

            with tempfile.TemporaryDirectory() as td:
                self.clone_root(base, td)
                e = RunEngine(td, self.DATE)
                fixture = self.write_fixture(Path(td) / "complete", e)
                run = start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                )
                data = self.data(td)
                self.assertEqual(data["classification"], "executor_binding_authorization_package_readiness_authorization_decision_complete")
                self.assertEqual(
                    data["classification_reason_codes"],
                    ["SYNTHETIC_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_AUTHORIZATION_DECISION_COMPLETE"],
                )
                self.assertEqual(
                    data["executor_binding_authorization_package_readiness_authorization_review_classification"],
                    "executor_binding_authorization_package_readiness_authorization_review_complete",
                )
                schema = json.loads((Path(__file__).resolve().parents[1] / "schemas" /
                    "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision.schema.json").read_text())
                for field in schema["required"] + schema["allOf"][0]["then"]["required"]:
                    self.assertIn(field, data)
                self.assertEqual(len(data["executor_binding_authorization_package_readiness_authorization_decision_evidence_ids"]), 10)
                self.assertEqual(len(set(data["executor_binding_authorization_package_readiness_authorization_decision_evidence_ids"])), 10)
                for position in range(1, 11):
                    receipt = e.store.read_json(
                        e.store.run_dir
                        / f"executor-binding-authorization-package-readiness-authorization-decision-evidence-{position:02d}.json"
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
                    "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
                )["content_digest"]
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                )
                artifact2 = e.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
                )["content_digest"]
                self.assertEqual(artifact1, artifact2)
                self.safe(data)

    def test_fail_closed_iteration29_identity_and_provenance_substitution(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)

            def mutate_artifact(engine, fn):
                artifact = engine.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
                )
                fn(artifact["data"])
                artifact["content_digest"] = semantic_digest(artifact)
                engine.store._atomic_write(
                    engine.store.artifact_path(
                        "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
                    ),
                    artifact,
                )

            cases = [
                lambda d: d.__setitem__("executor_binding_authorization_package_readiness_authorization_review_id", "sha256:" + "0" * 64),
                lambda d: d.__setitem__("executor_binding_authorization_package_readiness_authorization_review_policy_id", "changed"),
                lambda d: d.__setitem__("executor_binding_authorization_package_readiness_authorization_review_manifest_id", "changed"),
                lambda d: d.__setitem__("separate_executor_binding_authorization_package_readiness_authorization_review_id", "sha256:" + "1" * 64),
                lambda d: d.__setitem__("synthetic_binding_plan_descriptor_id", "sha256:" + "2" * 64),
                lambda d: d.__setitem__(
                    "executor_binding_authorization_package_readiness_authorization_review_evidence_ids",
                    list(reversed(d["executor_binding_authorization_package_readiness_authorization_review_evidence_ids"])),
                ),
                lambda d: d.__setitem__(
                    "executor_binding_authorization_package_readiness_authorization_review_evidence_ids",
                    [d["executor_binding_authorization_package_readiness_authorization_review_evidence_ids"][0]] * 10,
                ),
                lambda d: d.__setitem__(
                    "executor_binding_authorization_package_readiness_authorization_review_evidence_digests",
                    ["sha256:" + "3" * 64]
                    + d["executor_binding_authorization_package_readiness_authorization_review_evidence_digests"][1:],
                ),
            ]
            for idx, fn in enumerate(cases):
                with self.subTest(case=idx), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    mutate_artifact(engine, fn)
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=(
                                self.write_fixture(Path(td) / "fixture", engine)
                            ),
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                        )

    def test_fail_closed_iteration30_versions_source_capabilities_authority_and_cost(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)
            fixture_cases = {
                "schema": dict(mutate_policy=lambda p: p.update({"schema_version": "2.0.0"})),
                "policy-version": dict(
                    mutate_policy=lambda p: p.update(
                        {"executor_binding_authorization_package_readiness_authorization_decision_policy_version": "2.0.0"}
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
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                        )

            source_cases = {
                "endpoint": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"external_endpoint": "https://example.invalid"}
                ),
                "invocation": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"invocation_capability": True}
                ),
                "binding": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"real_executor_binding_capability": True}
                ),
                "command": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"executable_command": "echo unsafe"}
                ),
                "step": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"executable_steps": ["unsafe"]}
                ),
                "credential": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"credential_reference": "secret"}
                ),
                "target": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"deployment_target": "prod"}
                ),
                "paid": lambda d: d["synthetic_binding_plan_descriptor"].update(
                    {"paid_dependency_required": True}
                ),
                "mutation": lambda d: d.__setitem__("external_mutation_performed", True),
                "authority-flag": lambda d: d.__setitem__("production_action_authorized", True),
            }
            for name, mut in source_cases.items():
                with self.subTest(source=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    engine = RunEngine(td, self.DATE)
                    artifact = engine.store.load_artifact(
                        "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
                    )
                    mut(artifact["data"])
                    artifact["content_digest"] = semantic_digest(artifact)
                    engine.store._atomic_write(
                        engine.store.artifact_path(
                            "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
                        ),
                        artifact,
                    )
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                        )

    def test_fail_closed_reordered_duplicated_missing_substituted_corrupted_receipts(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)
            engine = RunEngine(base, self.DATE)
            fixture = self.write_fixture(Path(base) / "fixture", engine)
            start_daily_brief(
                self.DATE,
                state_root=base,
                integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
                integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
            )

            def expect_receipt_failure(mutator):
                with tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    mutator(e)
                    with self.assertRaises(
                        (
                            IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError,
                            IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionBoundaryFailure,
                        )
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=Path(td) / "fixture",
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                        )

            def mutate_final(e, fn):
                artifact = e.store.load_artifact(
                    "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
                )
                fn(artifact["data"])
                artifact["content_digest"] = semantic_digest(artifact)
                e.store._atomic_write(
                    e.store.artifact_path(
                        "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision"
                    ),
                    artifact,
                )

            expect_receipt_failure(
                lambda e: mutate_final(
                    e,
                    lambda d: d.__setitem__(
                        "executor_binding_authorization_package_readiness_authorization_decision_evidence_ids",
                        list(reversed(d["executor_binding_authorization_package_readiness_authorization_decision_evidence_ids"])),
                    ),
                )
            )
            expect_receipt_failure(
                lambda e: mutate_final(
                    e,
                    lambda d: d.__setitem__(
                        "executor_binding_authorization_package_readiness_authorization_decision_evidence_ids",
                        [d["executor_binding_authorization_package_readiness_authorization_decision_evidence_ids"][0]] * 10,
                    ),
                )
            )
            expect_receipt_failure(
                lambda e: mutate_final(
                    e,
                    lambda d: d.__setitem__(
                        "executor_binding_authorization_package_readiness_authorization_decision_evidence_ids",
                        d["executor_binding_authorization_package_readiness_authorization_decision_evidence_ids"][:-1],
                    ),
                )
            )

            def corrupt_receipt(e):
                path = e.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-evidence-05.json"
                r = e.store.read_json(path)
                r["source_executor_binding_authorization_package_readiness_authorization_review_evidence_id"] = "sha256:" + "9" * 64
                e.store._atomic_write(path, r)
            expect_receipt_failure(corrupt_receipt)

            def unsupported_receipt(e):
                path = e.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-evidence-05.json"
                r = e.store.read_json(path)
                r["receipt_version"] = "2.0.0"
                e.store._atomic_write(path, r)
            expect_receipt_failure(unsupported_receipt)

            def missing_receipt(e):
                (e.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-evidence-05.json").unlink()
            expect_receipt_failure(missing_receipt)

    def test_source_receipt_files_and_stale_upstream_fail_closed(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)
            engine = RunEngine(base, self.DATE)
            self.write_fixture(Path(base) / "fixture", engine)
            for case in ("reordered", "duplicated", "missing", "substituted", "corrupted", "version", "upstream-stale"):
                with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    p = e.store.run_dir / "executor-binding-authorization-package-readiness-authorization-review-evidence-05.json"
                    q = e.store.run_dir / "executor-binding-authorization-package-readiness-authorization-review-evidence-06.json"
                    if case == "missing":
                        p.unlink()
                    elif case == "reordered":
                        a, b = p.read_bytes(), q.read_bytes()
                        p.write_bytes(b)
                        q.write_bytes(a)
                    elif case == "duplicated":
                        p.write_bytes(q.read_bytes())
                    elif case == "upstream-stale":
                        a = e.store.load_artifact("production-integration-execution-executor-binding-preflight")
                        a["data"]["executor_binding_authorization_package_readiness_preflight_id"] = "changed"
                        a["content_digest"] = semantic_digest(a)
                        e.store._atomic_write(e.store.artifact_path(a["artifact_type"]), a)
                    else:
                        a = e.store.read_json(p)
                        if case == "version":
                            a["receipt_version"] = "9.0.0"
                        else:
                            a["credential_use_performed"] = True
                        if case == "substituted":
                            a["receipt_id"] = digest({k: v for k, v in a.items() if k != "receipt_id"})
                        e.store._atomic_write(p, a)
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(self.DATE, state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=Path(td) / "fixture",
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True)

    def test_changed_decision_cache_and_identity_fail_closed(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)
            engine = RunEngine(base, self.DATE)
            fixture = self.write_fixture(Path(base) / "fixture", engine)
            start_daily_brief(self.DATE, state_root=base,
                integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
                integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True)
            for case in ("cache", "artifact-version", "artifact-id", "record-id", "manifest-version"):
                with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    if case == "cache":
                        p = e.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-state.json"
                        a = e.store.read_json(p)
                        a["evaluation"]["classification"] = "blocked"
                    elif case.startswith("artifact"):
                        p = e.store.artifact_path("production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision")
                        a = e.store.read_json(p)
                        k = "executor_binding_authorization_package_readiness_authorization_decision_" + ("schema_version" if case.endswith("version") else "id")
                        a["data"][k] = "changed"
                        a["content_digest"] = semantic_digest(a)
                    elif case == "record-id":
                        p = Path(td) / "fixture" / "executor-binding-authorization-package-readiness-authorization-decision-record.json"
                        a = e.store.read_json(p)
                        a["authorization_decision_record_id"] = "changed"
                    else:
                        p = Path(td) / "fixture" / "executor-binding-authorization-package-readiness-authorization-decision-manifest.json"
                        a = e.store.read_json(p)
                        a["executor_binding_authorization_package_readiness_authorization_decision_manifest_version"] = "9.0.0"
                    e.store._atomic_write(p, a)
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(self.DATE, state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=Path(td) / "fixture",
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True)

    def recovery(self, source_root, boundary):
        temp = tempfile.TemporaryDirectory()
        root = temp.name
        self.clone_root(source_root, root)
        engine = RunEngine(root, self.DATE)
        counts = deepcopy(engine.store.load_run()["stage_executions"])
        locked = self.locked(engine)
        source_digest = engine.store.load_artifact(
            "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
        )["content_digest"]
        prior_files = self.snapshot(engine)
        fixture = self.write_fixture(Path(root) / "recovery", engine)
        failing = RunEngine(
            root,
            self.DATE,
            failure_injection=FailureInjection(
                "Complete", "synthetic_i30_failure", boundary
            ),
            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
        )
        with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionBoundaryFailure):
            failing.run()
        durable = {p.name: (p.read_bytes(), p.stat().st_mtime_ns)
                   for p in engine.store.run_dir.glob("executor-binding-authorization-package-readiness-authorization-decision-evidence-*.json")}
        start_daily_brief(
            self.DATE,
            state_root=root,
            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture,
            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
        )
        fresh = RunEngine(root, self.DATE)
        self.assertEqual(self.locked(fresh), locked)
        self.assertEqual(
            fresh.store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-authorization-review"
            )["content_digest"],
            source_digest,
        )
        for key, value in counts.items():
            self.assertEqual(fresh.store.load_run()["stage_executions"].get(key), value)
        self.assertEqual(
            fresh.store.read_json(
                fresh.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-incident.json"
            )["result"],
            "recovered",
        )
        self.assertEqual(prior_files, self.snapshot(fresh))
        for name, value in durable.items():
            p = fresh.store.run_dir / name
            self.assertEqual(value, (p.read_bytes(), p.stat().st_mtime_ns))
        state = fresh.store.read_json(fresh.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-state.json")
        self.emit("recovery", {"boundary": boundary, "attempts": state["attempts"],
                  "metrics": state["metrics"], "prior_durable_decision_evidence": len(durable),
                  "locked_upstream_artifact_count": len(locked), "upstream_reexecution": 0,
                  "iteration29_rebuilds": 0, "unrelated_record_rewrites": 0,
                  "full_pipeline_restarts": 0, "fresh_engine_resume": True})
        return temp, fresh

    def test_targeted_recovery_fresh_engine_no_rework(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)

            temp, engine = self.recovery(base, "executor_binding_authorization_package_readiness_authorization_decision:evaluation")
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-state.json"
            )
            self.assertEqual(state["attempts"]["evaluation"], 2)
            temp.cleanup()

            temp, engine = self.recovery(base, "executor_binding_authorization_package_readiness_authorization_decision:receipt:5")
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-state.json"
            )
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 4)
            self.assertEqual(len(state["receipt_digests"]), 10)
            temp.cleanup()

            temp, engine = self.recovery(
                base, "executor_binding_authorization_package_readiness_authorization_decision:final_executor_binding_authorization_package_readiness_authorization_decision_artifact"
            )
            state = engine.store.read_json(
                engine.store.run_dir / "executor-binding-authorization-package-readiness-authorization-decision-state.json"
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
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                )
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_review_only=True,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                )
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                )
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision.schema.json"
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
                counts, engine = self.make_executor_binding_authorization_package_readiness_authorization_review(
                    td, date, "shadow"
                )
                locked = self.locked(engine)
                prior_files = self.snapshot(engine)
                run = start_daily_brief(
                    date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                )
                data = self.data(td, date, "shadow")
                self.safe(data)
                self.assertEqual(
                    self.locked(RunEngine(td, date, mode="shadow")), locked
                )
                for key, value in counts.items():
                    self.assertEqual(run["stage_executions"].get(key), value)
                self.assertEqual(prior_files, self.snapshot(engine))
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(data["classification_reason_codes"][0], "ITERATION29_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_AUTHORIZATION_REVIEW_BLOCKED")
                artifact = engine.store.load_artifact("production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision")
                self.emit("exit_run", {"date": date, "mode": "shadow", "artifact_digest": artifact["content_digest"],
                          "decision_id": data["executor_binding_authorization_package_readiness_authorization_decision_id"],
                          "source_digest": data["executor_binding_authorization_package_readiness_authorization_review_artifact_digest"],
                          "classification": data["classification"], "reason_codes": data["classification_reason_codes"],
                          "locked_upstream_artifact_count": len(locked), "upstream_reexecution": 0,
                          "iteration29_rebuilds": 0, "unrelated_record_rewrites": 0, "full_pipeline_restarts": 0,
                          "real_executor_bound": data["real_executor_bound"], "real_executor_invoked": data["real_executor_invoked"],
                          "real_target_contacted": data["real_target_contacted"], "external_mutation": data["external_mutation_performed"],
                          "credential_use_authorized": data["credentials_use_authorized"]})
                outcomes.append(
                    (
                        data["classification"],
                        tuple(data["classification_reason_codes"]),
                        data["executor_binding_authorization_package_readiness_authorization_decision_id"],
                    )
                )
        self.assertEqual(outcomes[0][0], "blocked")
        self.assertEqual(outcomes[0][0:2], outcomes[1][0:2])
        self.assertEqual(outcomes[1][0:2], outcomes[2][0:2])

    def test_decision_record_exact_inventory_and_all_bound_identities(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)
            e = RunEngine(base, self.DATE)
            fixture = self.write_fixture(Path(base) / "fixture", e)
            original = json.loads((fixture / "executor-binding-authorization-package-readiness-authorization-decision-record.json").read_text())
            changes = {k: "sha256:" + "f" * 64 for k in original
                       if k.endswith(("_id", "_digest")) and k != "authorization_decision_record_id"}
            changes.update(noop=False, non_live=False, synthetic_only=False,
                           approved=False, grants_executor_binding_authority=True,
                           grants_executor_invocation_authority=True, external_mutation_permitted=True)
            for field in ("executor_binding_authorization_package_readiness_authorization_review_evidence_ids",
                          "executor_binding_authorization_package_readiness_authorization_review_evidence_digests"):
                values = original[field]
                for label, value in (("reordered", values[::-1]), ("duplicated", [values[0]]*10),
                                     ("missing", values[:-1]), ("substituted", ["changed"]+values[1:])):
                    changes[field + ":" + label] = value
            for name, value in changes.items():
                with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    path = Path(td) / "fixture" / "executor-binding-authorization-package-readiness-authorization-decision-record.json"
                    record = deepcopy(original)
                    record[name.split(":")[0]] = value
                    record["authorization_decision_record_id"] = digest({k:v for k,v in record.items() if k != "authorization_decision_record_id"})
                    path.write_text(json.dumps(record))
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(self.DATE, state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=path.parent)

    def test_inherited_iteration28_receipts_and_transitive_identities_fail_closed(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base, qualified=True)
            self.write_fixture(Path(base) / "fixture", RunEngine(base, self.DATE))
            for case in ("reorder", "duplicate", "missing", "substitute", "corrupt", "version"):
                with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    p = e.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-receipt-05.json"
                    q = e.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-receipt-06.json"
                    if case == "missing": p.unlink()
                    elif case == "duplicate": p.write_bytes(q.read_bytes())
                    elif case == "reorder":
                        left, right = p.read_bytes(), q.read_bytes()
                        p.write_bytes(right); q.write_bytes(left)
                    else:
                        record = e.store.read_json(p)
                        record["receipt_version" if case == "version" else "executor_binding_authorization_package_readiness_preflight_id"] = "changed"
                        if case == "substitute":
                            record["receipt_id"] = digest({k:v for k,v in record.items() if k != "receipt_id"})
                        e.store._atomic_write(p, record)
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(self.DATE, state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=Path(td)/"fixture")
            # Every ancestor's semantic mutation is rejected even when its own envelope is rehashed.
            for name in self.locked(RunEngine(base, self.DATE)):
                with self.subTest(ancestor=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    artifact = e.store.load_artifact(name)
                    artifact["data"]["changed_identity"] = True
                    artifact["content_digest"] = semantic_digest(artifact)
                    e.store._atomic_write(e.store.artifact_path(name), artifact)
                    with self.assertRaises(Exception):
                        start_daily_brief(self.DATE, state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=Path(td)/"fixture")

    def test_unsafe_unknown_fields_and_all_mutations_rejected_on_blocked_source(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_executor_binding_authorization_package_readiness_authorization_review(base)
            fields = {"external_endpoint": "https://example.invalid", "binding_capability": True,
                      "invocation_capability": True, "executable_command": "unsafe",
                      "executable_step": True, "credential": "synthetic-secret-marker",
                      "target": "production", "authority": True, "paid_dependency": "paid"}
            gate = ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecision
            fields.update({k: True for k in (*gate.AUTHORITY_FLAGS, *gate.MUTATION_FLAGS)})
            for name, value in fields.items():
                with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    fixture = self.write_fixture(Path(td)/"fixture", e, include_record=False,
                        mutate_manifest=lambda m: m.update({name: value}))
                    with self.assertRaises(IntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationDecisionError):
                        start_daily_brief(self.DATE, state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only=True,
                            integration_execution_executor_binding_authorization_package_readiness_authorization_decision_fixture_root=fixture)

    def test_all_bounded_modes_exclusive_and_prior_gate_never_prepared_or_built(self):
        import inspect
        from unittest.mock import patch
        from new_daily_ai_brief.integration_execution_executor_binding_authorization_package_readiness_authorization_review import ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessAuthorizationReview as Prior
        option = "integration_execution_executor_binding_authorization_package_readiness_authorization_decision_only"
        for name in inspect.signature(RunEngine).parameters:
            if name.endswith("_only") and name != option:
                with self.subTest(mode=name), tempfile.TemporaryDirectory() as td:
                    with self.assertRaises(ValueError):
                        RunEngine(td, self.DATE, **{name: True, option: True})
        with tempfile.TemporaryDirectory() as td:
            self.make_executor_binding_authorization_package_readiness_authorization_review(td)
            with patch.object(Prior, "prepare", side_effect=AssertionError("prior evaluation forbidden")), patch.object(Prior, "build_executor_binding_authorization_package_readiness_authorization_review", side_effect=AssertionError("prior rebuild forbidden")):
                start_daily_brief(self.DATE, state_root=td, **{option: True})


if __name__ == "__main__":
    unittest.main()
