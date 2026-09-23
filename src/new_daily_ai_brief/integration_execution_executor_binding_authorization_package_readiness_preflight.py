from __future__ import annotations

import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_EVIDENCE_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_POLICY_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_SCHEMA_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_EVIDENCE_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_POLICY_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_RECORD_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION,
)
from .integration_execution_executor_binding_authorization_package_readiness import (
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessBoundaryFailure,
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessError,
    ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadiness,
)
from .store import digest, semantic_digest


IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError = (
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessError
)
IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure = (
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessBoundaryFailure
)


class ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflight(
    ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadiness
):
    """Deterministic synthetic-only Iteration 27 readiness-preflight gate."""

    ARTIFACT_TYPE = (
        "production-integration-execution-executor-binding-authorization-package-readiness-preflight"
    )
    SOURCE_ARTIFACT_TYPE = (
        "production-integration-execution-executor-binding-authorization-package-readiness"
    )

    SOURCE_OUTPUT_FIELDS = {
        "executor_binding_authorization_package_readiness_id",
        "real_integration_steps_enabled",
        "real_integration_steps_executed",
        "final_state",
        "final_status",
        "completion_scope",
        "synthetic_only",
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

    POLICY_KEYS = {
        "schema_version",
        "executor_binding_authorization_package_readiness_preflight_policy_version",
        "policy_id",
        "synthetic_only",
        "allowed_upstream_classification",
        "classifications",
        "require_separate_authorization_package_readiness_preflight_record",
        "require_exactly_ten_readiness_evidence_records",
        "real_executor_binding_permitted",
        "real_executor_invocation_permitted",
        "real_authority_permitted",
        "zero_incremental_cost_required",
    }

    MANIFEST_KEYS = {
        "schema_version",
        "executor_binding_authorization_package_readiness_preflight_manifest_version",
        "manifest_id",
        "synthetic_only",
        "production_action_authorized",
        "production_cutover_authorized",
        "legacy_decommission_authorized",
        "production_publication",
        "real_executor_invocation_authorized",
        "credentials_use_authorized",
        "real_target_contact_authorized",
        "rollback_execution_authorized",
        "real_integration_steps_enabled",
        "executor_binding_authorization_package_readiness_binding",
        "evidence",
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

    EVIDENCE_KEYS = {
        "executor_declaration",
        "credential_declaration",
        "target_declaration",
        "rollback_declaration",
        "stop_abort_conditions",
        "cost_declaration",
    }

    RECORD_KEYS = {
        "schema_version",
        "record_version",
        "record_kind",
        "authorization_package_readiness_preflight_record_id",
        "decision",
        "approved",
        "noop",
        "non_live",
        "scope",
        "synthetic_only",
        "bound_upstream_identity",
        "bound_upstream_identity_digest",
        "executor_binding_authorization_package_readiness_artifact_digest",
        "executor_binding_authorization_package_readiness_id",
        "executor_binding_authorization_package_readiness_evidence_ids",
        "executor_binding_authorization_package_readiness_evidence_digests",
        "executor_binding_authorization_package_readiness_evidence_set_digest",
        "iteration24_semantic_identity_digest",
        "iteration25_semantic_identity_digest",
        "iteration26_semantic_identity_digest",
        "canonical_chain_digest",
        "executor_binding_authorization_package_readiness_preflight_manifest_id",
        "grants_production_authority",
        "grants_executor_binding_authority",
        "grants_executor_invocation_authority",
        "grants_credential_use_authority",
        "grants_real_target_contact_authority",
        "grants_rollback_execution_authority",
        "grants_cutover_authority",
        "grants_decommission_authority",
        "grants_publication_authority",
        "external_mutation_permitted",
        "zero_incremental_cost_approved",
        "production_action_authorized",
        "production_cutover_authorized",
        "legacy_decommission_authorized",
        "production_publication",
        "real_executor_invocation_authorized",
        "credentials_use_authorized",
        "real_target_contact_authorized",
        "rollback_execution_authorized",
        "real_integration_steps_enabled",
    }

    def __init__(
        self,
        store,
        edition_date: str,
        mode: str,
        fixture_root: Path | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = (
            "synthetic_integration_execution_executor_binding_authorization_package_"
            "readiness_preflight_boundary_failure"
        ),
    ):
        super().__init__(
            store,
            edition_date,
            mode,
            fixture_root,
            failure_boundary_id=None,
            failure_class=failure_class,
        )
        self.failure_boundary_id = (
            failure_boundary_id.removeprefix(
                "executor_binding_authorization_package_readiness_preflight:"
            )
            if failure_boundary_id
            else None
        )
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = (
            self.store.run_dir
            / "executor-binding-authorization-package-readiness-preflight-state.json"
        )
        self.metrics_path = (
            self.store.run_dir
            / "executor-binding-authorization-package-readiness-preflight-metrics.json"
        )
        self.incident_path = (
            self.store.run_dir
            / "executor-binding-authorization-package-readiness-preflight-incident.json"
        )

    def _source_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            key: deepcopy(value)
            for key, value in data.items()
            if key not in self.SOURCE_OUTPUT_FIELDS
        }

    def _bound_upstream_identity(
        self,
        artifact: dict[str, Any],
        data: dict[str, Any],
        validations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        semantic_identity = self._source_identity(data)
        return {
            **deepcopy(semantic_identity),
            "executor_binding_authorization_package_readiness_artifact_digest": artifact[
                "content_digest"
            ],
            "executor_binding_authorization_package_readiness_id": data[
                "executor_binding_authorization_package_readiness_id"
            ],
            "executor_binding_authorization_package_readiness_classification": data[
                "classification"
            ],
            "executor_binding_authorization_package_readiness_reason_codes": deepcopy(
                data.get("classification_reason_codes") or []
            ),
            "executor_binding_authorization_package_readiness_evidence_ids": deepcopy(
                data.get("executor_binding_authorization_package_readiness_evidence_ids")
                or []
            ),
            "executor_binding_authorization_package_readiness_evidence_digests": deepcopy(
                data.get(
                    "executor_binding_authorization_package_readiness_evidence_digests"
                )
                or []
            ),
            "executor_binding_authorization_package_readiness_evidence_set_digest": digest(
                validations
            ),
            "iteration26_semantic_identity": semantic_identity,
            "iteration26_semantic_identity_digest": digest(semantic_identity),
        }

    def _context(self, run: dict[str, Any]) -> dict[str, Any]:
        if self.mode not in {"synthetic", "shadow"}:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "synthetic/shadow only"
            )
        prior = ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadiness(
            self.store, self.edition_date, self.mode, None
        )
        prior_context = prior._context(run)
        self._validate_locked_chain(self.SOURCE_ARTIFACT_TYPE, set())
        artifact = self._locked(self.SOURCE_ARTIFACT_TYPE)
        data = artifact["data"]
        state = self.store.read_json(prior.state_path) or {}
        evaluation = state.get("evaluation") or {}
        if (
            not evaluation
            or digest(evaluation) != state.get("evaluation_digest")
            or evaluation.get("input_identity") != state.get("input_identity")
            or evaluation.get("bound_upstream_identity")
            != prior_context["bound_upstream_identity"]
            or evaluation.get("bound_upstream_identity_digest")
            != prior_context["bound_upstream_identity_digest"]
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "Iteration 26 durable readiness identity is stale or corrupted"
            )
        if (
            data.get("executor_binding_authorization_package_readiness_schema_version")
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_SCHEMA_VERSION
            or data.get(
                "executor_binding_authorization_package_readiness_policy_version"
            )
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_POLICY_VERSION
            or data.get("executor_binding_authorization_package_readiness_policy_id")
            != (
                "production-integration-execution-executor-binding-authorization-package-"
                "readiness-v1"
            )
            or data.get("executor_binding_authorization_package_readiness_manifest_id")
            != (
                "production-integration-execution-executor-binding-authorization-package-"
                "readiness-manifest-v1"
            )
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "unsupported Iteration 26 readiness identity/version"
            )
        validations: list[dict[str, Any]] = []
        for position, source in enumerate(
            prior_context["source_executor_binding_authorization_package_evidence"],
            start=1,
        ):
            if (
                evaluation["classification"]
                != "executor_binding_authorization_package_readiness_complete"
            ):
                break
            record = self.store.read_json(prior._receipt_path(position))
            expected_record = prior._receipt_record(
                prior_context, evaluation, position, source
            )
            if record != expected_record:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    f"Iteration 26 readiness evidence changed/missing at position {position}"
                )
            validations.append(record)
        expected = prior._artifact_data(
            {
                **deepcopy(evaluation),
                "executor_binding_authorization_package_readiness_evidence_records": validations,
            }
        )
        if data != expected:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "Iteration 26 locked readiness differs from exact durable evidence"
            )
        prior.finalize(artifact)
        bound = self._bound_upstream_identity(artifact, data, validations)
        return {
            "executor_binding_authorization_package_readiness_artifact": artifact,
            "executor_binding_authorization_package_readiness_data": data,
            "source_executor_binding_authorization_package_readiness_evidence": validations,
            "bound_upstream_identity": bound,
            "bound_upstream_identity_digest": digest(bound),
        }

    def _validate_policy_manifest(
        self, policy: dict[str, Any], manifest: dict[str, Any]
    ) -> None:
        if set(policy) != self.POLICY_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "Iteration 27 policy contains unsupported fields"
            )
        if set(manifest) != self.MANIFEST_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "Iteration 27 manifest contains unsupported fields"
            )
        if (
            policy.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION
            or policy.get(
                "executor_binding_authorization_package_readiness_preflight_policy_version"
            )
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_POLICY_VERSION
            or policy.get("policy_id")
            != (
                "production-integration-execution-executor-binding-authorization-package-"
                "readiness-preflight-v1"
            )
            or policy.get("synthetic_only") is not True
            or policy.get("allowed_upstream_classification")
            != "executor_binding_authorization_package_readiness_complete"
            or policy.get("classifications")
            != [
                "blocked",
                "executor_binding_authorization_package_readiness_preflight_complete",
                "invalid",
            ]
            or policy.get(
                "require_separate_authorization_package_readiness_preflight_record"
            )
            is not True
            or policy.get("require_exactly_ten_readiness_evidence_records") is not True
            or policy.get("real_executor_binding_permitted") is not False
            or policy.get("real_executor_invocation_permitted") is not False
            or policy.get("real_authority_permitted") is not False
            or policy.get("zero_incremental_cost_required") is not True
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "unsupported or unsafe Iteration 27 readiness-preflight policy"
            )
        if (
            manifest.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION
            or manifest.get(
                "executor_binding_authorization_package_readiness_preflight_manifest_version"
            )
            != "1.0.0"
            or manifest.get("manifest_id")
            != (
                "production-integration-execution-executor-binding-authorization-package-"
                "readiness-preflight-manifest-v1"
            )
            or manifest.get("synthetic_only") is not True
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "unsupported Iteration 27 readiness-preflight manifest"
            )
        self._assert_no_authority(manifest, "Iteration 27 manifest")
        binding = manifest.get(
            "executor_binding_authorization_package_readiness_binding"
        )
        if not isinstance(binding, dict):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "invalid readiness binding"
            )
        if binding and set(binding) != {
            "binding_mode",
            "executor_binding_authorization_package_readiness_artifact_digest",
            "executor_binding_authorization_package_readiness_id",
            "executor_binding_authorization_package_readiness_policy_id",
            "executor_binding_authorization_package_readiness_policy_digest",
            "executor_binding_authorization_package_readiness_manifest_id",
            "executor_binding_authorization_package_readiness_manifest_digest",
            "separate_executor_binding_authorization_package_readiness_id",
            "separate_executor_binding_authorization_package_readiness_digest",
            "executor_binding_authorization_package_readiness_evidence_ids",
            "executor_binding_authorization_package_readiness_evidence_digests",
            "executor_binding_authorization_package_readiness_evidence_set_digest",
            "iteration24_semantic_identity_digest",
            "iteration25_semantic_identity_digest",
            "iteration26_semantic_identity_digest",
            "canonical_chain_digest",
            "bound_upstream_identity_digest",
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "unsupported readiness binding fields"
            )
        evidence = manifest.get("evidence") or {}
        if set(evidence) != self.EVIDENCE_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "Iteration 27 manifest evidence contains unsupported fields"
            )
        if evidence.get("executor_declaration") != {
            "real_executor_required": False,
            "real_executor_present": False,
            "real_executor_bound": False,
            "real_executor_invocable": False,
            "real_executor_invocation_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "executor declaration is not synthetic-only"
            )
        if evidence.get("credential_declaration") != {
            "production_credentials_required": False,
            "production_credentials_present": False,
            "production_credentials_stored": False,
            "credentials_use_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "credential declaration is not fail-closed"
            )
        if evidence.get("target_declaration") != {
            "scope": "synthetic_non_production",
            "real_target_present": False,
            "real_target_contacted": False,
            "real_target_contact_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "target declaration is not fail-closed"
            )
        if evidence.get("rollback_declaration") != {
            "rollback_plan_bound": True,
            "rollback_execution_authorized": False,
            "rollback_executed": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "rollback declaration is not fail-closed"
            )
        if evidence.get("cost_declaration") != {
            "incremental_paid_dependency_required": False,
            "zero_incremental_cost_approved": True,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "repository-authoritative zero-incremental-cost approval missing"
            )
        required = {
            "identity_mismatch",
            "authority_flag_true",
            "cost_guard_failed",
            "provenance_validation_mismatch",
            "readiness_record_missing",
            "readiness_evidence_missing",
            "readiness_evidence_corrupted",
            "real_executor_binding_capability_present",
            "executor_invocation_capability_present",
            "credential_present",
            "target_present",
            "executable_command_present",
            "executable_step_present",
            "external_mutation_present",
        }
        if set(evidence.get("stop_abort_conditions") or []) != required:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "readiness-preflight stop/abort conditions incomplete"
            )

    def _record_binding(
        self,
        record: dict[str, Any] | None,
        context: dict[str, Any],
        manifest: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None]:
        if record is None:
            return {
                "authorization_package_readiness_preflight_record_id": None,
                "authorization_package_readiness_preflight_record_digest": None,
            }, "EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_RECORD_MISSING"
        if set(record) != self.RECORD_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "readiness-preflight record contains unsupported fields"
            )
        body = deepcopy(record)
        supplied = body.pop("authorization_package_readiness_preflight_record_id")
        if supplied != digest(body):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "readiness-preflight record semantic identity changed"
            )
        bound = context["bound_upstream_identity"]
        expected = {
            "schema_version": (
                EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION
            ),
            "record_version": (
                EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_RECORD_VERSION
            ),
            "record_kind": (
                "production-integration-execution-executor-binding-authorization-package-"
                "readiness-preflight-record"
            ),
            "decision": (
                "complete_synthetic_executor_binding_authorization_package_readiness_preflight"
            ),
            "approved": True,
            "noop": True,
            "non_live": True,
            "scope": "execution_executor_binding_authorization_package_readiness_preflight_only",
            "synthetic_only": True,
            "bound_upstream_identity": bound,
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
            "executor_binding_authorization_package_readiness_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_id": bound[
                "executor_binding_authorization_package_readiness_id"
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
            "executor_binding_authorization_package_readiness_preflight_manifest_id": manifest[
                "manifest_id"
            ],
            "grants_production_authority": False,
            "grants_executor_binding_authority": False,
            "grants_executor_invocation_authority": False,
            "grants_credential_use_authority": False,
            "grants_real_target_contact_authority": False,
            "grants_rollback_execution_authority": False,
            "grants_cutover_authority": False,
            "grants_decommission_authority": False,
            "grants_publication_authority": False,
            "external_mutation_permitted": False,
            "zero_incremental_cost_approved": True,
            "production_action_authorized": False,
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "production_publication": False,
            "real_executor_invocation_authorized": False,
            "credentials_use_authorized": False,
            "real_target_contact_authorized": False,
            "rollback_execution_authorized": False,
            "real_integration_steps_enabled": 0,
        }
        for key, value in expected.items():
            if digest(record.get(key)) != digest(value):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    f"readiness-preflight record binding changed: {key}"
                )
        return {
            "authorization_package_readiness_preflight_record_id": supplied,
            "authorization_package_readiness_preflight_record_digest": digest(record),
        }, None

    def _policy_manifest_record(
        self, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        policy = self._read_json_fixture(
            "executor-binding-authorization-package-readiness-preflight-policy.json"
        )
        manifest = self._read_json_fixture(
            "executor-binding-authorization-package-readiness-preflight-manifest.json"
        )
        record = self._read_json_fixture(
            "executor-binding-authorization-package-readiness-preflight-record.json",
            optional=True,
        )
        assert policy is not None and manifest is not None
        self._validate_policy_manifest(policy, manifest)
        if record is not None:
            self._record_binding(record, context, manifest)
        return policy, manifest, record

    def _evaluate(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        record: dict[str, Any] | None,
    ) -> dict[str, Any]:
        bound = context["bound_upstream_identity"]
        source = bound[
            "executor_binding_authorization_package_readiness_classification"
        ]
        reasons = bound[
            "executor_binding_authorization_package_readiness_reason_codes"
        ]
        expected_source_binding = {
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
        binding = manifest.get(
            "executor_binding_authorization_package_readiness_binding"
        )
        if binding != expected_source_binding and not (
            binding == {} and source in {"blocked", "invalid"}
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "readiness-preflight manifest binds a different Iteration 26 identity"
            )
        if source == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION26_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_INVALID",
                    *reasons,
                ],
                "decision_binding": {
                    "authorization_package_readiness_preflight_record_id": None,
                    "authorization_package_readiness_preflight_record_digest": None,
                },
            }
        if source == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION26_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_BLOCKED",
                    *reasons,
                ],
                "decision_binding": {
                    "authorization_package_readiness_preflight_record_id": None,
                    "authorization_package_readiness_preflight_record_digest": None,
                },
            }
        decision_binding, reason = self._record_binding(record, context, manifest)
        if reason:
            return {
                "classification": "blocked",
                "classification_reason_codes": [reason],
                "decision_binding": decision_binding,
            }
        return {
            "classification": (
                "executor_binding_authorization_package_readiness_preflight_complete"
            ),
            "classification_reason_codes": [
                "SYNTHETIC_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_COMPLETE"
            ],
            "decision_binding": decision_binding,
        }

    def _input_identity(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        record: dict[str, Any] | None,
    ) -> dict[str, Any]:
        bound = context["bound_upstream_identity"]
        return {
            "executor_binding_authorization_package_readiness_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_id": bound[
                "executor_binding_authorization_package_readiness_id"
            ],
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
            "executor_binding_authorization_package_readiness_preflight_policy_digest": digest(
                policy
            ),
            "executor_binding_authorization_package_readiness_preflight_manifest_digest": digest(
                manifest
            ),
            "authorization_package_readiness_preflight_record_digest": (
                digest(record) if record else None
            ),
            "authorization_package_readiness_preflight_record_id": (
                record.get("authorization_package_readiness_preflight_record_id")
                if record
                else None
            ),
        }

    def _receipt_path(self, position: int) -> Path:
        return (
            self.store.run_dir
            / f"executor-binding-authorization-package-readiness-preflight-evidence-{position:02d}.json"
        )

    def _receipt_record(
        self,
        context: dict[str, Any],
        evaluated: dict[str, Any],
        position: int,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        bound = context["bound_upstream_identity"]
        body = {
            "schema_version": (
                EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION
            ),
            "receipt_version": (
                EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_EVIDENCE_VERSION
            ),
            "executor_binding_authorization_package_readiness_id": bound[
                "executor_binding_authorization_package_readiness_id"
            ],
            "executor_binding_authorization_package_readiness_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_preflight_record_id": evaluated[
                "decision_binding"
            ]["authorization_package_readiness_preflight_record_id"],
            "position": position,
            "source_executor_binding_authorization_package_readiness_evidence_id": source[
                "receipt_id"
            ],
            "source_executor_binding_authorization_package_readiness_evidence_digest": digest(
                source
            ),
            "noop_verified": True,
            "side_effect_free_verified": True,
            "real_executor_binding_performed": False,
            "real_executor_invocation_performed": False,
            "credential_use_performed": False,
            "real_target_contact_performed": False,
            "network_side_effect_performed": False,
            "production_write_performed": False,
            "rollback_execution_performed": False,
            "cutover_execution_performed": False,
            "decommission_execution_performed": False,
            "publication_execution_performed": False,
            "external_mutation_performed": False,
            "executable_command": None,
            "executable_step": False,
        }
        return {**body, "receipt_id": digest(body)}

    def _ensure_receipts(
        self,
        context: dict[str, Any],
        evaluated: dict[str, Any],
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if (
            evaluated["classification"]
            != "executor_binding_authorization_package_readiness_preflight_complete"
        ):
            return []
        sources = context[
            "source_executor_binding_authorization_package_readiness_evidence"
        ]
        if len(sources) != 10:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "preflight-complete requires ten Iteration 26 readiness validations"
            )
        final_locked = self.store.load_artifact(self.ARTIFACT_TYPE)
        receipts: list[dict[str, Any]] = []
        for position, source in enumerate(sources, start=1):
            expected = self._receipt_record(context, evaluated, position, source)
            path = self._receipt_path(position)
            existing = self.store.read_json(path)
            key = str(position)
            state["attempts"]["receipts"].setdefault(key, 0)
            if existing is not None:
                if existing != expected:
                    raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                        f"cached readiness-preflight evidence changed at position {position}"
                    )
                state["metrics"]["receipt_reuse"] += 1
                state["receipt_digests"][key] = digest(existing)
                receipts.append(existing)
                continue
            if final_locked is not None and final_locked.get("status") == "locked":
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    f"locked preflight artifact is missing evidence at position {position}"
                )
            state["attempts"]["receipts"][key] += 1
            state["metrics"]["receipt_build_attempts"] += 1
            self._save_state(state)
            boundary = f"validation:{position}"
            if self.failure_boundary_id == boundary and not self._failure_fired:
                self._failure_fired = True
                self._record_incident(boundary, state)
                self._write_metrics(state)
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure(
                    "executor_binding_authorization_package_readiness_preflight_evidence_validation",
                    boundary,
                    self.failure_class,
                )
            self.store._atomic_write(path, expected)
            state["receipt_digests"][key] = digest(expected)
            self._save_state(state)
            receipts.append(expected)
        if len(receipts) != 10:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "preflight-complete must produce exactly ten receipts"
            )
        return receipts

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        context = self._context(run)
        policy, manifest, record = self._policy_manifest_record(context)
        identity = self._input_identity(context, policy, manifest, record)
        state = self._load_state(identity)
        state["metrics"]["validation_checks"] += 1
        if state.get("evaluation") is None:
            state["attempts"]["evaluation"] += 1
            state["metrics"]["evaluation_attempts"] += 1
            self._save_state(state)
            if self.failure_boundary_id == "evaluation" and not self._failure_fired:
                self._failure_fired = True
                self._record_incident("evaluation", state)
                self._write_metrics(state)
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure(
                    "executor_binding_authorization_package_readiness_preflight_evaluation",
                    "evaluation",
                    self.failure_class,
                )
            outcome = self._evaluate(context, policy, manifest, record)
            state["evaluation"] = {
                **outcome,
                "input_identity": deepcopy(identity),
                "bound_upstream_identity": deepcopy(
                    context["bound_upstream_identity"]
                ),
                "bound_upstream_identity_digest": context[
                    "bound_upstream_identity_digest"
                ],
                "executor_binding_authorization_package_readiness_preflight_policy_id": policy[
                    "policy_id"
                ],
                "executor_binding_authorization_package_readiness_preflight_policy_version": policy[
                    "executor_binding_authorization_package_readiness_preflight_policy_version"
                ],
                "executor_binding_authorization_package_readiness_preflight_manifest_id": manifest[
                    "manifest_id"
                ],
                "evidence": deepcopy(manifest["evidence"]),
            }
            state["evaluation_digest"] = digest(state["evaluation"])
            self._save_state(state)
        else:
            if digest(state["evaluation"]) != state.get("evaluation_digest"):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "cached preflight evaluation corrupted"
                )
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        receipts = self._ensure_receipts(context, evaluated, state)
        evaluated[
            "executor_binding_authorization_package_readiness_preflight_evidence_records"
        ] = receipts
        state["metrics"]["elapsed_ms"] = max(
            0, int((time.monotonic() - started) * 1000)
        )
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
        return evaluated

    def _artifact_data(self, evaluated: dict[str, Any]) -> dict[str, Any]:
        decision_binding = evaluated["decision_binding"]
        receipts = evaluated[
            "executor_binding_authorization_package_readiness_preflight_evidence_records"
        ]
        evidence = evaluated["evidence"]
        if (
            evaluated["classification"]
            == "executor_binding_authorization_package_readiness_preflight_complete"
        ):
            if len(receipts) != 10:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "preflight-complete requires ten no-op receipts"
                )
            if len({x["receipt_id"] for x in receipts}) != 10:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "preflight evidence identities must be unique"
                )
        elif receipts:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "blocked or invalid preflight cannot carry evidence"
            )
        identity = {
            "executor_binding_authorization_package_readiness_preflight_schema_version": (
                EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION
            ),
            "executor_binding_authorization_package_readiness_preflight_policy_version": evaluated[
                "executor_binding_authorization_package_readiness_preflight_policy_version"
            ],
            "executor_binding_authorization_package_readiness_preflight_policy_id": evaluated[
                "executor_binding_authorization_package_readiness_preflight_policy_id"
            ],
            "executor_binding_authorization_package_readiness_preflight_policy_digest": evaluated[
                "input_identity"
            ][
                "executor_binding_authorization_package_readiness_preflight_policy_digest"
            ],
            "executor_binding_authorization_package_readiness_preflight_manifest_id": evaluated[
                "executor_binding_authorization_package_readiness_preflight_manifest_id"
            ],
            "executor_binding_authorization_package_readiness_preflight_manifest_digest": evaluated[
                "input_identity"
            ][
                "executor_binding_authorization_package_readiness_preflight_manifest_digest"
            ],
            "separate_executor_binding_authorization_package_readiness_preflight_id": decision_binding[
                "authorization_package_readiness_preflight_record_id"
            ],
            "separate_executor_binding_authorization_package_readiness_preflight_digest": decision_binding[
                "authorization_package_readiness_preflight_record_digest"
            ],
            **deepcopy(evaluated["bound_upstream_identity"]),
            "bound_upstream_identity_digest": evaluated[
                "bound_upstream_identity_digest"
            ],
            "executor_binding_authorization_package_readiness_preflight_evidence_ids": [
                x["receipt_id"] for x in receipts
            ],
            "executor_binding_authorization_package_readiness_preflight_evidence_digests": [
                digest(x) for x in receipts
            ],
            "executor_binding_authorization_package_readiness_preflight_evidence_set_digest": digest(
                receipts
            ),
            "executor_declaration": deepcopy(evidence["executor_declaration"]),
            "credential_declaration": deepcopy(evidence["credential_declaration"]),
            "target_declaration": deepcopy(evidence["target_declaration"]),
            "rollback_declaration": deepcopy(evidence["rollback_declaration"]),
            "stop_abort_conditions": deepcopy(evidence["stop_abort_conditions"]),
            "cost_declaration": deepcopy(evidence["cost_declaration"]),
            "classification": evaluated["classification"],
            "classification_reason_codes": deepcopy(
                evaluated["classification_reason_codes"]
            ),
        }
        return {
            **identity,
            "executor_binding_authorization_package_readiness_preflight_id": digest(
                identity
            ),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": (
                "synthetic_shadow_execution_executor_binding_authorization_package_"
                "readiness_preflight_only"
            ),
            "synthetic_only": True,
            "production_action_authorized": False,
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "production_publication": False,
            "real_executor_invocation_authorized": False,
            "credentials_use_authorized": False,
            "real_target_contact_authorized": False,
            "rollback_execution_authorized": False,
            "real_executor_bound": False,
            "real_executor_invoked": False,
            "production_credentials_present": False,
            "production_credentials_stored": False,
            "real_target_contacted": False,
            "rollback_executed": False,
            "cutover_executed": False,
            "decommission_executed": False,
            "publication_executed": False,
            "external_mutation_performed": False,
            "real_private_command_center_mutated": False,
            "public_site_mutated": False,
            "production_schedule_action": False,
            "subscriber_delivery_changed": False,
            "legacy_content_migrated": False,
            "readers_routed_to_greenfield": False,
            "legacy_repository_modified": False,
            "incremental_paid_dependency_added": False,
            "lifecycle_state_changed": False,
        }

    def validate_existing(
        self,
        existing: dict[str, Any] | None,
        run: dict[str, Any],
        evaluated: dict[str, Any],
    ) -> None:
        if existing is None:
            return
        if (
            existing.get("status") != "locked"
            or semantic_digest(existing) != existing.get("content_digest")
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure(
                "executor_binding_authorization_package_readiness_preflight_validation",
                "executor_binding_authorization_package_readiness_preflight_artifact",
                "cached readiness-preflight artifact invalid",
            )
        if existing.get("data") != self._artifact_data(evaluated):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure(
                "executor_binding_authorization_package_readiness_preflight_validation",
                "executor_binding_authorization_package_readiness_preflight_artifact",
                "cached readiness-preflight artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_executor_binding_authorization_package_readiness_preflight(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        boundary = (
            "final_executor_binding_authorization_package_readiness_preflight_artifact"
        )
        if self.failure_boundary_id == boundary and not self._failure_fired:
            self._failure_fired = True
            self._record_incident(boundary, state)
            self._write_metrics(state)
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightBoundaryFailure(
                "executor_binding_authorization_package_readiness_preflight_artifact_assembly",
                boundary,
                self.failure_class,
            )
        return self._artifact_data(evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "final readiness-preflight artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "final readiness-preflight artifact digest invalid"
            )
        data = artifact.get("data") or {}
        self._assert_no_authority(data, "Iteration 27 artifact")
        for flag in (
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
            if data.get(flag) is not False:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    f"readiness preflight cannot perform {flag}"
                )
        classification = data.get("classification")
        if (
            classification
            == "executor_binding_authorization_package_readiness_preflight_complete"
        ):
            if (
                data.get(
                    "executor_binding_authorization_package_readiness_classification"
                )
                != "executor_binding_authorization_package_readiness_complete"
            ):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "preflight-complete requires complete Iteration 26 readiness"
                )
            if not data.get(
                "separate_executor_binding_authorization_package_readiness_preflight_id"
            ):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "preflight-complete requires separate preflight record"
                )
            ids = list(
                data.get(
                    "executor_binding_authorization_package_readiness_preflight_evidence_ids"
                )
                or []
            )
            digests = list(
                data.get(
                    "executor_binding_authorization_package_readiness_preflight_evidence_digests"
                )
                or []
            )
            if len(ids) != 10 or len(digests) != 10:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "preflight-complete requires ten receipts"
                )
            if len(ids) != len(set(ids)) or len(digests) != len(set(digests)):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "preflight evidence inventory contains duplicates"
                )
            loaded: list[dict[str, Any]] = []
            for position, (expected_id, expected_digest) in enumerate(
                zip(ids, digests), start=1
            ):
                receipt = self.store.read_json(self._receipt_path(position))
                if receipt is None:
                    raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                        f"preflight evidence missing at position {position}"
                    )
                if (
                    receipt.get("receipt_id") != expected_id
                    or digest(receipt) != expected_digest
                    or receipt.get("position") != position
                    or receipt.get("receipt_version")
                    != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_EVIDENCE_VERSION
                    or receipt.get("noop_verified") is not True
                    or receipt.get("side_effect_free_verified") is not True
                    or receipt.get("real_executor_binding_performed") is not False
                    or receipt.get("real_executor_invocation_performed") is not False
                    or receipt.get("credential_use_performed") is not False
                    or receipt.get("real_target_contact_performed") is not False
                    or receipt.get("network_side_effect_performed") is not False
                    or receipt.get("production_write_performed") is not False
                    or receipt.get("rollback_execution_performed") is not False
                    or receipt.get("cutover_execution_performed") is not False
                    or receipt.get("decommission_execution_performed") is not False
                    or receipt.get("publication_execution_performed") is not False
                    or receipt.get("external_mutation_performed") is not False
                    or receipt.get("executable_command") is not None
                    or receipt.get("executable_step") is not False
                ):
                    raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                        f"unsafe or corrupted preflight evidence at position {position}"
                    )
                loaded.append(receipt)
            if digest(loaded) != data.get(
                "executor_binding_authorization_package_readiness_preflight_evidence_set_digest"
            ):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                    "preflight evidence set digest changed"
                )
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessPreflightError(
                "unsupported readiness-preflight classification"
            )
