from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_executor_binding_authorization_package_readiness_preflight import (
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure,
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError,
    ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflight,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration26


class Iteration27ExecutorBindingAuthorizationPackageReadinessPreflightTest(
    unittest.TestCase
):
    DATE = "2026-09-22"

    def helper(self):
        return test_iteration26.Iteration26ExecutorBindingAuthorizationPackageReadinessTest(
            methodName="test_current_repository_stays_blocked_deterministic_and_zero_rework"
        )

    def fixture(self, name):
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration27" / name

    def make_source(self, root, date=DATE, mode="synthetic", qualified=False):
        h = self.helper()
        _, engine = h.make_source(root, date, mode, qualified=qualified)
        kwargs = {}
        if qualified:
            kwargs[
                "integration_execution_executor_binding_authorization_package_readiness_fixture_root"
            ] = h.write_fixture(Path(root) / "i26-qualified", engine)
        run = start_daily_brief(
            date,
            mode=mode,
            state_root=root,
            integration_execution_executor_binding_authorization_package_readiness_only=True,
            **kwargs,
        )
        return deepcopy(run["stage_executions"]), RunEngine(root, date, mode=mode)

    def locked(self, engine):
        values = self.helper().locked(engine)
        values[
            "production-integration-execution-executor-binding-authorization-package-readiness"
        ] = engine.store.load_artifact(
            "production-integration-execution-executor-binding-authorization-package-readiness"
        )["content_digest"]
        return values

    def data(self, root, date=DATE, mode="synthetic"):
        return RunEngine(root, date, mode=mode).store.load_artifact(
            "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
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
        src = self.fixture(
            "synthetic-executor-binding-authorization-package-readiness-preflight-complete"
        )
        policy = json.loads(
            (
                src
                / "executor-binding-authorization-package-readiness-preflight-policy.json"
            ).read_text()
        )
        manifest = json.loads(
            (
                src
                / "executor-binding-authorization-package-readiness-preflight-manifest.json"
            ).read_text()
        )
        record = json.loads(
            (
                src
                / "executor-binding-authorization-package-readiness-preflight-record.json"
            ).read_text()
        )
        gate = ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflight(
            engine.store, engine.edition_date, engine.mode, root
        )
        context = gate._context(engine.store.load_run())
        bound = context["bound_upstream_identity"]
        manifest["executor_binding_authorization_package_readiness_binding"] = {
            "binding_mode": "exact_locked_executor_binding_authorization_package_readiness_artifact",
            "executor_binding_authorization_package_readiness_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_id": bound[
                "executor_binding_authorization_package_readiness_id"
            ],
            "executor_binding_authorization_package_readiness_policy_id": bound[
                "executor_binding_authorization_package_readiness_policy_id"
            ],
            "executor_binding_authorization_package_readiness_policy_digest": bound[
                "executor_binding_authorization_package_readiness_policy_digest"
            ],
            "executor_binding_authorization_package_readiness_manifest_id": bound[
                "executor_binding_authorization_package_readiness_manifest_id"
            ],
            "executor_binding_authorization_package_readiness_manifest_digest": bound[
                "executor_binding_authorization_package_readiness_manifest_digest"
            ],
            "separate_executor_binding_authorization_package_readiness_id": bound[
                "separate_executor_binding_authorization_package_readiness_id"
            ],
            "separate_executor_binding_authorization_package_readiness_digest": bound[
                "separate_executor_binding_authorization_package_readiness_digest"
            ],
            "executor_binding_authorization_package_readiness_evidence_ids": bound[
                "executor_binding_authorization_package_readiness_evidence_ids"
            ],
            "executor_binding_authorization_package_readiness_evidence_digests": bound[
                "executor_binding_authorization_package_readiness_evidence_digests"
            ],
            "executor_binding_authorization_package_readiness_evidence_set_digest": bound[
                "executor_binding_authorization_package_readiness_evidence_set_digest"
            ],
            "iteration24_semantic_identity_digest": bound[
                "iteration24_semantic_identity_digest"
            ],
            "iteration25_semantic_identity_digest": bound[
                "iteration25_semantic_identity_digest"
            ],
            "iteration26_semantic_identity_digest": bound[
                "iteration26_semantic_identity_digest"
            ],
            "canonical_chain_digest": bound["canonical_chain_digest"],
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
        }
        for key in list(record):
            if key in bound:
                record[key] = deepcopy(bound[key])
        # The Iteration 27 record binds the complete Iteration 26 semantic identity
        # separately from the inherited Iteration 26 -> Iteration 25 bound digest.
        record["bound_upstream_identity"] = deepcopy(bound)
        record["bound_upstream_identity_digest"] = context[
            "bound_upstream_identity_digest"
        ]
        record[
            "executor_binding_authorization_package_readiness_preflight_manifest_id"
        ] = manifest["manifest_id"]
        if mutate_policy:
            mutate_policy(policy)
        if mutate_manifest:
            mutate_manifest(manifest)
        if mutate_record:
            mutate_record(record)
        body = deepcopy(record)
        body.pop("authorization_package_readiness_preflight_record_id", None)
        record["authorization_package_readiness_preflight_record_id"] = digest(body)
        (
            root
            / "executor-binding-authorization-package-readiness-preflight-policy.json"
        ).write_text(json.dumps(policy))
        (
            root
            / "executor-binding-authorization-package-readiness-preflight-manifest.json"
        ).write_text(json.dumps(manifest))
        if include_record:
            (
                root
                / "executor-binding-authorization-package-readiness-preflight-record.json"
            ).write_text(json.dumps(record))
        return root

    def clone_root(self, source, destination):
        shutil.copytree(source, destination, dirs_exist_ok=True)

    def snapshot_upstream(self, engine):
        result = {}
        for path in engine.store.run_dir.rglob("*.json"):
            name = path.name
            if name in {"run.json", "lease.json"}:
                continue
            if name.startswith(
                "executor-binding-authorization-package-readiness-preflight"
            ):
                continue
            if (
                name
                == "production-integration-execution-executor-binding-authorization-package-readiness-preflight.json"
            ):
                continue
            result[str(path.relative_to(engine.store.run_dir))] = (
                path.read_bytes(),
                path.stat().st_mtime_ns,
            )
        return result

    def test_current_repository_stays_blocked_deterministic_and_zero_rework(self):
        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_source(td)
            locked = self.locked(engine)
            before = self.snapshot_upstream(engine)
            first = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
            )
            data1 = self.data(td)
            digest1 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
            )["content_digest"]
            second = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
            )
            data2 = self.data(td)
            digest2 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
            )["content_digest"]
            self.assertEqual(data1["classification"], "blocked")
            self.assertEqual(
                data1["classification_reason_codes"][0],
                "ITERATION26_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_BLOCKED",
            )
            self.assertEqual(
                data1["executor_binding_authorization_package_readiness_preflight_id"],
                data2["executor_binding_authorization_package_readiness_preflight_id"],
            )
            self.assertEqual(digest1, digest2)
            self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
            self.assertEqual(before, self.snapshot_upstream(RunEngine(td, self.DATE)))
            for key, value in counts.items():
                self.assertEqual(first["stage_executions"].get(key), value)
                self.assertEqual(second["stage_executions"].get(key), value)
            self.safe(data1)

    def test_preflight_complete_requires_separate_record_and_exact_transitive_binding(self):
        with tempfile.TemporaryDirectory() as base:
            counts, engine = self.make_source(base, qualified=True)
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
                    integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )
                data = self.data(td)
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(
                    data["classification_reason_codes"],
                    [
                        "EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_RECORD_MISSING"
                    ],
                )
            with tempfile.TemporaryDirectory() as td:
                self.clone_root(base, td)
                e = RunEngine(td, self.DATE)
                fixture = self.write_fixture(Path(td) / "complete", e)
                run = start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )
                data = self.data(td)
                self.assertEqual(
                    data["classification"],
                    "executor_binding_authorization_package_readiness_preflight_complete",
                )
                self.assertEqual(
                    data["classification_reason_codes"],
                    [
                        "SYNTHETIC_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_COMPLETE"
                    ],
                )
                self.assertEqual(
                    data[
                        "executor_binding_authorization_package_readiness_classification"
                    ],
                    "executor_binding_authorization_package_readiness_complete",
                )
                self.assertEqual(
                    len(
                        data[
                            "executor_binding_authorization_package_readiness_preflight_evidence_ids"
                        ]
                    ),
                    10,
                )
                self.assertEqual(
                    len(
                        data[
                            "executor_binding_authorization_package_readiness_evidence_ids"
                        ]
                    ),
                    10,
                )
                self.assertEqual(
                    len(data["executor_binding_authorization_package_evidence_ids"]),
                    10,
                )
                self.assertEqual(
                    len(data["executor_binding_authorization_decision_evidence_ids"]),
                    10,
                )
                self.assertTrue(
                    data["iteration24_semantic_identity_digest"].startswith("sha256:")
                )
                self.assertTrue(
                    data["iteration25_semantic_identity_digest"].startswith("sha256:")
                )
                self.assertTrue(
                    data["iteration26_semantic_identity_digest"].startswith("sha256:")
                )
                self.assertTrue(
                    data[
                        "separate_executor_binding_authorization_package_readiness_preflight_id"
                    ].startswith("sha256:")
                )
                self.assertEqual(self.locked(RunEngine(td, self.DATE)), locked)
                for key, value in counts.items():
                    self.assertEqual(run["stage_executions"].get(key), value)
                self.safe(data)

    def test_complete_replay_is_deterministic_and_reuses_preflight_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            counts, engine = self.make_source(td, qualified=True)
            fixture = self.write_fixture(Path(td) / "complete", engine)
            first = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
                integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
            )
            artifact1 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
            )
            second = start_daily_brief(
                self.DATE,
                state_root=td,
                integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
                integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
            )
            artifact2 = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
            )
            self.assertEqual(artifact1["content_digest"], artifact2["content_digest"])
            self.assertEqual(artifact1["data"], artifact2["data"])
            state = RunEngine(td, self.DATE).store.read_json(
                RunEngine(td, self.DATE).store.run_dir
                / "executor-binding-authorization-package-readiness-preflight-state.json"
            )
            self.assertGreaterEqual(state["metrics"]["evaluation_reuse"], 1)
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 10)
            for key, value in counts.items():
                self.assertEqual(first["stage_executions"].get(key), value)
                self.assertEqual(second["stage_executions"].get(key), value)

    def test_fail_closed_unsafe_manifest_record_versions_cost_and_capabilities(self):
        mutations = [
            (
                "policy-version",
                "policy",
                lambda x: x.__setitem__(
                    "executor_binding_authorization_package_readiness_preflight_policy_version",
                    "2.0.0",
                ),
            ),
            (
                "real-executor",
                "manifest",
                lambda x: x["evidence"]["executor_declaration"].__setitem__(
                    "real_executor_present", True
                ),
            ),
            (
                "invocable",
                "manifest",
                lambda x: x["evidence"]["executor_declaration"].__setitem__(
                    "real_executor_invocable", True
                ),
            ),
            (
                "credential",
                "manifest",
                lambda x: x["evidence"]["credential_declaration"].__setitem__(
                    "production_credentials_present", True
                ),
            ),
            (
                "target",
                "manifest",
                lambda x: x["evidence"]["target_declaration"].__setitem__(
                    "real_target_present", True
                ),
            ),
            (
                "paid",
                "manifest",
                lambda x: x["evidence"]["cost_declaration"].__setitem__(
                    "incremental_paid_dependency_required", True
                ),
            ),
            (
                "missing-zero-cost-approval",
                "manifest",
                lambda x: x["evidence"]["cost_declaration"].__setitem__(
                    "zero_incremental_cost_approved", False
                ),
            ),
            (
                "authority",
                "record",
                lambda x: x.__setitem__("grants_production_authority", True),
            ),
            (
                "record-zero-cost",
                "record",
                lambda x: x.__setitem__("zero_incremental_cost_approved", False),
            ),
            (
                "record-version",
                "record",
                lambda x: x.__setitem__("record_version", "2.0.0"),
            ),
        ]
        for name, target, mutation in mutations:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_source(td, qualified=True)
                kwargs = {"mutate_" + target: mutation}
                fixture = self.write_fixture(Path(td) / name, engine, **kwargs)
                with self.assertRaises(
                    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
                ):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
                        integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                    )

    def test_fail_closed_source_evidence_missing_corrupted_reordered_and_duplicated(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_source(td, qualified=True)
            p1 = (
                engine.store.run_dir
                / "executor-binding-authorization-package-readiness-evidence-01.json"
            )
            record = json.loads(p1.read_text())
            record["position"] = 2
            p1.write_text(json.dumps(record))
            with self.assertRaises(
                IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
            ):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )

        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_source(td, qualified=True)
            p2 = (
                engine.store.run_dir
                / "executor-binding-authorization-package-readiness-evidence-02.json"
            )
            p2.unlink()
            with self.assertRaises(
                IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
            ):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )

        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_source(td, qualified=True)
            p1 = (
                engine.store.run_dir
                / "executor-binding-authorization-package-readiness-evidence-01.json"
            )
            p2 = (
                engine.store.run_dir
                / "executor-binding-authorization-package-readiness-evidence-02.json"
            )
            p2.write_bytes(p1.read_bytes())
            with self.assertRaises(
                IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
            ):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )

        with tempfile.TemporaryDirectory() as td:
            _, engine = self.make_source(td, qualified=True)
            artifact = engine.store.load_artifact(
                "production-integration-execution-executor-binding-authorization-package-readiness"
            )
            ids = artifact["data"][
                "executor_binding_authorization_package_readiness_evidence_ids"
            ]
            ids[0], ids[1] = ids[1], ids[0]
            artifact["content_digest"] = semantic_digest(artifact)
            engine.store._atomic_write(
                engine.store.artifact_path(
                    "production-integration-execution-executor-binding-authorization-package-readiness"
                ),
                artifact,
            )
            with self.assertRaises(
                IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
            ):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )

    def test_changed_iteration26_and_transitive_identities_fail_closed(self):
        cases = {
            "schema-version": lambda d: d.__setitem__(
                "executor_binding_authorization_package_readiness_schema_version",
                "2.0.0",
            ),
            "readiness-id": lambda d: d.__setitem__(
                "executor_binding_authorization_package_readiness_id",
                "sha256:changed",
            ),
            "package-id": lambda d: d.__setitem__(
                "executor_binding_authorization_package_id", "sha256:changed"
            ),
            "decision-id": lambda d: d.__setitem__(
                "executor_binding_authorization_decision_id", "sha256:changed"
            ),
            "iteration25": lambda d: d.__setitem__(
                "iteration25_semantic_identity_digest", "sha256:changed"
            ),
            "iteration24": lambda d: d.__setitem__(
                "iteration24_semantic_identity_digest", "sha256:changed"
            ),
            "authority": lambda d: d.__setitem__(
                "production_action_authorized", True
            ),
            "executor": lambda d: d.__setitem__("real_executor_bound", True),
        }
        with tempfile.TemporaryDirectory() as base:
            self.make_source(base, qualified=True)
            for name, mutate in cases.items():
                with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    artifact = e.store.load_artifact(
                        "production-integration-execution-executor-binding-authorization-package-readiness"
                    )
                    mutate(artifact["data"])
                    artifact["content_digest"] = semantic_digest(artifact)
                    e.store._atomic_write(
                        e.store.artifact_path(
                            "production-integration-execution-executor-binding-authorization-package-readiness"
                        ),
                        artifact,
                    )
                    with self.assertRaises(
                        IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                        )

    def test_preflight_record_exact_binding_and_unknown_unsafe_fields_fail_closed(self):
        record_cases = {
            "bound-digest": lambda r: r.__setitem__(
                "bound_upstream_identity_digest", "sha256:changed"
            ),
            "iteration26": lambda r: r.__setitem__(
                "iteration26_semantic_identity_digest", "sha256:changed"
            ),
            "source-id": lambda r: r.__setitem__(
                "executor_binding_authorization_package_readiness_id",
                "sha256:changed",
            ),
            "source-evidence": lambda r: r.__setitem__(
                "executor_binding_authorization_package_readiness_evidence_ids",
                list(
                    reversed(
                        r[
                            "executor_binding_authorization_package_readiness_evidence_ids"
                        ]
                    )
                ),
            ),
        }
        for name, mutation in record_cases.items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                _, engine = self.make_source(td, qualified=True)
                fixture = self.write_fixture(
                    Path(td) / name, engine, mutate_record=mutation
                )
                with self.assertRaises(
                    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
                ):
                    start_daily_brief(
                        self.DATE,
                        state_root=td,
                        integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
                        integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                    )

        unsafe = {
            "external_endpoint": "https://example.invalid",
            "binding_capability": True,
            "invocation_capability": True,
            "executable_command": "unsafe",
            "executable_step": True,
            "credential": "synthetic-secret-marker",
            "target": "production",
            "authority": True,
            "paid_dependency": "paid",
            "real_private_command_center_mutated": True,
            "public_site_mutated": True,
            "production_schedule_action": True,
            "subscriber_delivery_changed": True,
            "legacy_content_migrated": True,
            "readers_routed_to_greenfield": True,
            "legacy_repository_modified": True,
            "incremental_paid_dependency_added": True,
            "lifecycle_state_changed": True,
        }
        with tempfile.TemporaryDirectory() as base:
            self.make_source(base, qualified=True)
            for name, value in unsafe.items():
                with self.subTest(name=name), tempfile.TemporaryDirectory() as td:
                    self.clone_root(base, td)
                    e = RunEngine(td, self.DATE)
                    fixture = self.write_fixture(
                        Path(td) / "unsafe",
                        e,
                        mutate_manifest=lambda m, n=name, v=value: m.update({n: v}),
                    )
                    with self.assertRaises(
                        IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError
                    ):
                        start_daily_brief(
                            self.DATE,
                            state_root=td,
                            integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
                            integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                        )

    def recovery(self, source_root, boundary):
        temp = tempfile.TemporaryDirectory()
        root = temp.name
        self.clone_root(source_root, root)
        engine = RunEngine(root, self.DATE)
        counts = deepcopy(engine.store.load_run()["stage_executions"])
        locked = self.locked(engine)
        upstream = self.snapshot_upstream(engine)
        fixture = self.write_fixture(Path(root) / "recovery", engine)
        failing = RunEngine(
            root,
            self.DATE,
            failure_injection=FailureInjection(
                "Complete", "synthetic_i27_failure", boundary
            ),
            integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
            integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
        )
        with self.assertRaises(
            IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure
        ):
            failing.run()
        durable = {
            p.name: (p.read_bytes(), p.stat().st_mtime_ns)
            for p in engine.store.run_dir.glob(
                "executor-binding-authorization-package-readiness-preflight-evidence-*.json"
            )
        }
        start_daily_brief(
            self.DATE,
            state_root=root,
            integration_execution_executor_binding_authorization_package_readiness_preflight_fixture_root=fixture,
            integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
        )
        fresh = RunEngine(root, self.DATE)
        self.assertEqual(self.locked(fresh), locked)
        self.assertEqual(upstream, self.snapshot_upstream(fresh))
        for key, value in counts.items():
            self.assertEqual(fresh.store.load_run()["stage_executions"].get(key), value)
        incident = fresh.store.read_json(
            fresh.store.run_dir
            / "executor-binding-authorization-package-readiness-preflight-incident.json"
        )
        self.assertEqual(incident["result"], "recovered")
        for name, value in durable.items():
            p = fresh.store.run_dir / name
            self.assertEqual(value, (p.read_bytes(), p.stat().st_mtime_ns))
        return temp, fresh

    def test_targeted_recovery_fresh_engine_reuses_durable_evidence_without_rework(self):
        with tempfile.TemporaryDirectory() as base:
            self.make_source(base, qualified=True)

            temp, engine = self.recovery(
                base,
                "executor_binding_authorization_package_readiness_preflight:evaluation",
            )
            state = engine.store.read_json(
                engine.store.run_dir
                / "executor-binding-authorization-package-readiness-preflight-state.json"
            )
            self.assertEqual(state["attempts"]["evaluation"], 2)
            temp.cleanup()

            temp, engine = self.recovery(
                base,
                "executor_binding_authorization_package_readiness_preflight:validation:5",
            )
            state = engine.store.read_json(
                engine.store.run_dir
                / "executor-binding-authorization-package-readiness-preflight-state.json"
            )
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 4)
            self.assertEqual(len(state["receipt_digests"]), 10)
            temp.cleanup()

            temp, engine = self.recovery(
                base,
                "executor_binding_authorization_package_readiness_preflight:"
                "final_executor_binding_authorization_package_readiness_preflight_artifact",
            )
            state = engine.store.read_json(
                engine.store.run_dir
                / "executor-binding-authorization-package-readiness-preflight-state.json"
            )
            self.assertEqual(state["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state["metrics"]["receipt_reuse"], 10)
            temp.cleanup()

    def test_three_independent_shadow_exit_runs_are_stable_blocked_and_safe(self):
        outcomes = []
        for date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                counts, engine = self.make_source(td, date, "shadow")
                locked = self.locked(engine)
                before = self.snapshot_upstream(engine)
                run = start_daily_brief(
                    date,
                    mode="shadow",
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )
                data = self.data(td, date, "shadow")
                self.assertEqual(data["classification"], "blocked")
                self.assertEqual(
                    data["classification_reason_codes"][0],
                    "ITERATION26_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_BLOCKED",
                )
                self.assertEqual(
                    self.locked(RunEngine(td, date, mode="shadow")), locked
                )
                self.assertEqual(
                    before,
                    self.snapshot_upstream(RunEngine(td, date, mode="shadow")),
                )
                for key, value in counts.items():
                    self.assertEqual(run["stage_executions"].get(key), value)
                self.safe(data)
                outcomes.append(
                    (
                        data["classification"],
                        tuple(data["classification_reason_codes"]),
                    )
                )
        self.assertEqual(outcomes[0], outcomes[1])
        self.assertEqual(outcomes[1], outcomes[2])

    def test_bounded_mode_is_mutually_exclusive_and_production_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                RunEngine(
                    td,
                    self.DATE,
                    integration_execution_executor_binding_authorization_package_readiness_only=True,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    mode="production",
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )
            with self.assertRaises(Exception):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_execution_executor_binding_authorization_package_readiness_preflight_only=True,
                )

    def test_schema_requires_preflight_record_and_ten_evidence_items(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-execution-executor-binding-authorization-package-readiness-preflight.schema.json"
            ).read_text()
        )
        self.assertIn(
            "executor_binding_authorization_package_readiness_preflight_complete",
            schema["properties"]["classification"]["enum"],
        )
        for branch in schema.get("allOf", []):
            then = branch.get("then", {})
            if (
                "separate_executor_binding_authorization_package_readiness_preflight_id"
                in then.get("required", [])
            ):
                props = then["properties"]
                self.assertEqual(
                    props[
                        "executor_binding_authorization_package_readiness_preflight_evidence_ids"
                    ]["minItems"],
                    10,
                )
                self.assertEqual(
                    props[
                        "executor_binding_authorization_package_readiness_preflight_evidence_ids"
                    ]["maxItems"],
                    10,
                )
                break
        else:
            self.fail("schema does not require the separate readiness-preflight record")
