from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_POLICY_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_POLICY_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_RECEIPT_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_RECORD_VERSION,
    EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest


class IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(ContractError):
    pass


class IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure(
    IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError
):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id


class ProductionIntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsal:
    """Deterministic synthetic-only Iteration 28 authorization-package-readiness rehearsal gate."""

    ARTIFACT_TYPE = "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal"
    SOURCE_ARTIFACT_TYPE = "production-integration-execution-executor-binding-authorization-package-readiness-preflight"

    AUTHORITY_FLAGS = (
        "production_action_authorized",
        "production_cutover_authorized",
        "legacy_decommission_authorized",
        "production_publication",
        "real_executor_invocation_authorized",
        "credentials_use_authorized",
        "real_target_contact_authorized",
        "rollback_execution_authorized",
    )
    MUTATION_FLAGS = (
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
    SOURCE_OUTPUT_FIELDS = {
        "executor_binding_authorization_package_readiness_preflight_id",
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
        *AUTHORITY_FLAGS,
        *MUTATION_FLAGS,
    }
    POLICY_KEYS = {
        "schema_version",
        "executor_binding_authorization_package_readiness_rehearsal_policy_version",
        "policy_id",
        "synthetic_only",
        "allowed_upstream_classification",
        "classifications",
        "require_separate_rehearsal_record",
        "require_exactly_ten_noop_receipts",
        "real_executor_binding_permitted",
        "real_executor_invocation_permitted",
        "real_authority_permitted",
        "zero_incremental_cost_required",
    }
    MANIFEST_KEYS = {
        "schema_version",
        "executor_binding_authorization_package_readiness_rehearsal_manifest_version",
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
        "executor_binding_authorization_package_readiness_preflight_binding",
        "evidence",
        *MUTATION_FLAGS,
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
        "rehearsal_record_id",
        "decision",
        "approved",
        "scope",
        "synthetic_only",
        "noop",
        "non_live",
        "bound_upstream_identity",
        "executor_binding_authorization_package_readiness_preflight_artifact_digest",
        "executor_binding_authorization_package_readiness_preflight_id",
        "executor_binding_authorization_package_readiness_preflight_policy_id",
        "executor_binding_authorization_package_readiness_preflight_policy_digest",
        "executor_binding_authorization_package_readiness_preflight_manifest_id",
        "executor_binding_authorization_package_readiness_preflight_manifest_digest",
        "separate_executor_binding_authorization_package_readiness_preflight_id",
        "separate_executor_binding_authorization_package_readiness_preflight_digest",
        "synthetic_binding_plan_descriptor_id",
        "synthetic_binding_plan_descriptor_digest",
        "executor_binding_authorization_package_readiness_preflight_evidence_ids",
        "executor_binding_authorization_package_readiness_preflight_evidence_digests",
        "executor_binding_authorization_package_readiness_preflight_evidence_set_digest",
        "iteration24_semantic_identity_digest",
        "iteration25_semantic_identity_digest",
        "iteration26_semantic_identity_digest",
        "iteration27_semantic_identity_digest",
        "canonical_chain_digest",
        "bound_upstream_identity_digest",
        "executor_binding_authorization_package_readiness_rehearsal_manifest_id",
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
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_integration_execution_executor_binding_authorization_package_readiness_rehearsal_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = fixture_root
        self.failure_boundary_id = (
            failure_boundary_id.removeprefix("executor_binding_authorization_package_readiness_rehearsal:")
            if failure_boundary_id
            else None
        )
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-state.json"
        self.metrics_path = self.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-metrics.json"
        self.incident_path = self.store.run_dir / "executor-binding-authorization-package-readiness-rehearsal-incident.json"

    def _read_json_fixture(self, name: str, *, optional: bool = False) -> dict[str, Any] | None:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "production executor-binding rehearsal is intentionally unconfigured"
            )
        path = self.fixture_root / name
        if not path.exists():
            if optional:
                return None
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                f"executor-binding-authorization-package-readiness-rehearsal fixture missing: {name}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _locked(self, artifact_type: str) -> dict[str, Any]:
        artifact = self.store.load_artifact(artifact_type)
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                f"locked artifact missing: {artifact_type}"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                f"locked artifact corrupted: {artifact_type}"
            )
        return artifact

    def _assert_no_authority(self, record: dict[str, Any], label: str) -> None:
        for flag in (*self.AUTHORITY_FLAGS, *self.MUTATION_FLAGS):
            if record.get(flag) is not False:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"{label} must keep {flag}=false"
                )
        if record.get("real_integration_steps_enabled", 0) != 0:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                f"{label} cannot enable real integration steps"
            )
        if record.get("real_integration_steps_executed", 0) != 0:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                f"{label} cannot execute real integration steps"
            )

    def _source_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            key: deepcopy(value)
            for key, value in data.items()
            if key not in self.SOURCE_OUTPUT_FIELDS
        }

    def _source_validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"executor-binding-authorization-package-readiness-preflight-evidence-{position:02d}.json"

    def _load_source_validations(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        ids = list(data.get("executor_binding_authorization_package_readiness_preflight_evidence_ids") or [])
        digests = list(data.get("executor_binding_authorization_package_readiness_preflight_evidence_digests") or [])
        if len(ids) != len(digests):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 executor-binding-authorization-package-readiness-preflight provenance inventory length mismatch"
            )
        if len(ids) != len(set(ids)) or len(digests) != len(set(digests)):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 executor-binding-authorization-package-readiness-preflight provenance inventory contains duplicates"
            )
        classification = data.get("classification")
        if classification == "executor_binding_authorization_package_readiness_preflight_complete" and len(ids) != 10:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor_binding_authorization_package_readiness_preflight_complete requires ten Iteration 27 provenance validations"
            )
        if classification != "executor_binding_authorization_package_readiness_preflight_complete" and ids:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "non-qualified Iteration 27 input cannot carry provenance validations"
            )
        result: list[dict[str, Any]] = []
        for position, (expected_id, expected_digest) in enumerate(zip(ids, digests), start=1):
            record = self.store.read_json(self._source_validation_path(position))
            if record is None:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"Iteration 27 provenance validation missing at position {position}"
                )
            if record.get("receipt_id") != expected_id or digest(record) != expected_digest:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"Iteration 27 provenance validation changed at position {position}"
                )
            if (
                record.get("position") != position
                or record.get("noop_verified") is not True
                or record.get("side_effect_free_verified") is not True
                or record.get("real_executor_binding_performed") is not False
                or record.get("real_executor_invocation_performed") is not False
                or record.get("credential_use_performed") is not False
                or record.get("real_target_contact_performed") is not False
                or record.get("network_side_effect_performed") is not False
                or record.get("production_write_performed") is not False
                or record.get("rollback_execution_performed") is not False
                or record.get("cutover_execution_performed") is not False
                or record.get("decommission_execution_performed") is not False
                or record.get("publication_execution_performed") is not False
                or record.get("external_mutation_performed") is not False
                or record.get("executable_command") is not None
                or record.get("executable_step") is not False
            ):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"Iteration 27 provenance validation unsafe at position {position}"
                )
            result.append(record)
        return result

    def _bound_upstream_identity(
        self,
        artifact: dict[str, Any],
        data: dict[str, Any],
        validations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        semantic_identity = self._source_identity(data)
        return {
            **deepcopy(semantic_identity),
            "executor_binding_authorization_package_readiness_preflight_artifact_digest": artifact["content_digest"],
            "executor_binding_authorization_package_readiness_preflight_id": data["executor_binding_authorization_package_readiness_preflight_id"],
            "executor_binding_authorization_package_readiness_preflight_classification": data["classification"],
            "executor_binding_authorization_package_readiness_preflight_reason_codes": deepcopy(
                data.get("classification_reason_codes") or []
            ),
            "executor_binding_authorization_package_readiness_preflight_policy_id": data.get(
                "executor_binding_authorization_package_readiness_preflight_policy_id"
            ),
            "executor_binding_authorization_package_readiness_preflight_policy_digest": data.get(
                "executor_binding_authorization_package_readiness_preflight_policy_digest"
            ),
            "executor_binding_authorization_package_readiness_preflight_manifest_id": data.get(
                "executor_binding_authorization_package_readiness_preflight_manifest_id"
            ),
            "executor_binding_authorization_package_readiness_preflight_manifest_digest": data.get(
                "executor_binding_authorization_package_readiness_preflight_manifest_digest"
            ),
            "separate_executor_binding_authorization_package_readiness_preflight_id": data.get(
                "separate_executor_binding_authorization_package_readiness_preflight_id"
            ),
            "separate_executor_binding_authorization_package_readiness_preflight_digest": data.get(
                "separate_executor_binding_authorization_package_readiness_preflight_digest"
            ),
            "synthetic_binding_plan_descriptor_id": data.get(
                "synthetic_binding_plan_descriptor_id"
            ),
            "synthetic_binding_plan_descriptor_digest": data.get(
                "synthetic_binding_plan_descriptor_digest"
            ),
            "executor_binding_authorization_package_readiness_preflight_evidence_ids": deepcopy(
                data.get("executor_binding_authorization_package_readiness_preflight_evidence_ids") or []
            ),
            "executor_binding_authorization_package_readiness_preflight_evidence_digests": deepcopy(
                data.get("executor_binding_authorization_package_readiness_preflight_evidence_digests") or []
            ),
            "executor_binding_authorization_package_readiness_preflight_evidence_set_digest": digest(validations),
            "canonical_chain_digest": data.get("canonical_chain_digest"),
            "iteration27_semantic_identity": semantic_identity,
            "iteration27_semantic_identity_digest": digest(semantic_identity),
        }

    def _context(self, run: dict[str, Any]) -> dict[str, Any]:
        if (
            run.get("current_state") != "Complete"
            or run.get("completion_status") != "complete_locked"
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor-binding rehearsal requires Complete / complete_locked"
            )
        artifact = self._locked(self.SOURCE_ARTIFACT_TYPE)
        data = artifact.get("data") or {}
        if data.get("executor_binding_authorization_package_readiness_preflight_schema_version") != (
            EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_SCHEMA_VERSION
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "unsupported Iteration 27 executor-binding-authorization-package-readiness-preflight schema version"
            )
        if data.get("executor_binding_authorization_package_readiness_preflight_policy_version") != (
            EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_POLICY_VERSION
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "unsupported Iteration 27 executor-binding-authorization-package-readiness-preflight policy version"
            )
        if data.get("executor_binding_authorization_package_readiness_preflight_id") != digest(self._source_identity(data)):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 executor_binding_authorization_package_readiness_preflight_id does not match semantic identity"
            )
        self._assert_no_authority(data, "Iteration 27 executor-binding-authorization-package-readiness-preflight artifact")
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
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"Iteration 27 executor-binding-authorization-package-readiness-preflight artifact must keep {flag}=false"
                )
        if data.get("synthetic_only") is not True:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 executor-binding-authorization-package-readiness-preflight artifact must be synthetic-only"
            )
        if data.get("executor_binding_authorization_package_readiness_preflight_policy_id") != (
            "production-integration-execution-executor-binding-authorization-package-readiness-preflight-v1"
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 policy identity changed"
            )
        if data.get("executor_binding_authorization_package_readiness_preflight_manifest_id") != (
            "production-integration-execution-executor-binding-authorization-package-readiness-preflight-manifest-v1"
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 manifest identity changed"
            )
        classification = data.get("classification")
        if classification not in {
            "blocked",
            "executor_binding_authorization_package_readiness_preflight_complete",
            "invalid",
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "unsupported Iteration 27 classification"
            )
        if classification == "executor_binding_authorization_package_readiness_preflight_complete":
            if not data.get("separate_executor_binding_authorization_package_readiness_preflight_id"):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "qualified Iteration 27 input requires separate preflight identity"
                )
        state = self.store.read_json(
            self.store.run_dir / "executor-binding-authorization-package-readiness-preflight-state.json"
        )
        evaluation = (state or {}).get("evaluation") or {}
        input_identity = evaluation.get("input_identity") or {}
        decision_binding = evaluation.get("decision_binding") or {}
        if (
            not evaluation
            or digest(evaluation) != (state or {}).get("evaluation_digest")
            or evaluation.get("classification") != data.get("classification")
            or evaluation.get("classification_reason_codes")
            != data.get("classification_reason_codes")
            or evaluation.get("executor_binding_authorization_package_readiness_preflight_policy_id")
            != data.get("executor_binding_authorization_package_readiness_preflight_policy_id")
            or evaluation.get("executor_binding_authorization_package_readiness_preflight_manifest_id")
            != data.get("executor_binding_authorization_package_readiness_preflight_manifest_id")
            or input_identity.get("executor_binding_authorization_package_readiness_preflight_policy_digest")
            != data.get("executor_binding_authorization_package_readiness_preflight_policy_digest")
            or input_identity.get("executor_binding_authorization_package_readiness_preflight_manifest_digest")
            != data.get("executor_binding_authorization_package_readiness_preflight_manifest_digest")
            or decision_binding.get("authorization_package_readiness_preflight_record_id")
            != data.get("separate_executor_binding_authorization_package_readiness_preflight_id")
            or decision_binding.get("authorization_package_readiness_preflight_record_digest")
            != data.get("separate_executor_binding_authorization_package_readiness_preflight_digest")
            or evaluation.get("bound_upstream_identity_digest")
            != data.get("bound_upstream_identity_digest")
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 durable executor-binding-authorization-package-readiness-preflight provenance does not match locked artifact"
            )
        validations = self._load_source_validations(data)
        if digest(validations) != data.get(
            "executor_binding_authorization_package_readiness_preflight_evidence_set_digest"
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 27 preflight evidence set digest changed"
            )
        bound = self._bound_upstream_identity(artifact, data, validations)
        return {
            "executor_binding_authorization_package_readiness_preflight_artifact": artifact,
            "executor_binding_authorization_package_readiness_preflight_data": data,
            "source_executor_binding_authorization_package_readiness_preflight_evidence": validations,
            "bound_upstream_identity": bound,
            "bound_upstream_identity_digest": digest(bound),
        }

    def _validate_policy_manifest(
        self, policy: dict[str, Any], manifest: dict[str, Any]
    ) -> None:
        if set(policy) != self.POLICY_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 28 policy contains unsupported fields"
            )
        if set(manifest) != self.MANIFEST_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 28 manifest contains unsupported fields"
            )
        if (
            policy.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION
            or policy.get("executor_binding_authorization_package_readiness_rehearsal_policy_version")
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_POLICY_VERSION
            or policy.get("policy_id")
            != "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal-v1"
            or policy.get("synthetic_only") is not True
            or policy.get("allowed_upstream_classification")
            != "executor_binding_authorization_package_readiness_preflight_complete"
            or policy.get("classifications")
            != ["blocked", "executor_binding_authorization_package_readiness_rehearsal_complete", "invalid"]
            or policy.get("require_separate_rehearsal_record") is not True
            or policy.get("require_exactly_ten_noop_receipts") is not True
            or policy.get("real_executor_binding_permitted") is not False
            or policy.get("real_executor_invocation_permitted") is not False
            or policy.get("real_authority_permitted") is not False
            or policy.get("zero_incremental_cost_required") is not True
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "unsupported or unsafe Iteration 28 executor-binding-authorization-package-readiness-rehearsal policy"
            )
        if (
            manifest.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION
            or manifest.get("executor_binding_authorization_package_readiness_rehearsal_manifest_version") != "1.0.0"
            or manifest.get("manifest_id")
            != "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal-manifest-v1"
            or manifest.get("synthetic_only") is not True
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "unsupported Iteration 28 executor-binding-authorization-package-readiness-rehearsal manifest"
            )
        self._assert_no_authority(manifest, "Iteration 28 manifest")
        evidence = manifest.get("evidence") or {}
        if set(evidence) != self.EVIDENCE_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "Iteration 28 manifest evidence contains unsupported fields"
            )
        if evidence.get("executor_declaration") != {
            "real_executor_required": False,
            "real_executor_present": False,
            "real_executor_bound": False,
            "real_executor_invocable": False,
            "real_executor_invocation_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor declaration is not synthetic-only"
            )
        if evidence.get("credential_declaration") != {
            "production_credentials_required": False,
            "production_credentials_present": False,
            "production_credentials_stored": False,
            "credentials_use_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "credential declaration is not fail-closed"
            )
        if evidence.get("target_declaration") != {
            "scope": "synthetic_non_production",
            "real_target_present": False,
            "real_target_contacted": False,
            "real_target_contact_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "target declaration is not fail-closed"
            )
        if evidence.get("rollback_declaration") != {
            "rollback_plan_bound": True,
            "rollback_execution_authorized": False,
            "rollback_executed": False,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "rollback declaration is not fail-closed"
            )
        if evidence.get("cost_declaration") != {
            "incremental_paid_dependency_required": False,
            "zero_incremental_cost_approved": True,
        }:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "zero-incremental-cost approval missing"
            )
        required = {
            "identity_mismatch",
            "authority_flag_true",
            "cost_guard_failed",
            "preflight_evidence_mismatch",
            "rehearsal_record_missing",
            "rehearsal_receipt_missing",
            "rehearsal_receipt_corrupted",
            "real_executor_binding_capability_present",
            "executor_invocation_capability_present",
            "credential_present",
            "target_present",
            "executable_command_present",
            "executable_step_present",
            "external_mutation_present",
        }
        if set(evidence.get("stop_abort_conditions") or []) != required:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor-binding-authorization-package-readiness-rehearsal stop/abort conditions incomplete"
            )

    def _record_binding(
        self,
        record: dict[str, Any] | None,
        context: dict[str, Any],
        manifest: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None]:
        if record is None:
            return {
                "rehearsal_record_id": None,
                "rehearsal_record_digest": None,
            }, "EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_RECORD_MISSING"
        if set(record) != self.RECORD_KEYS:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor-binding-authorization-package-readiness-rehearsal record contains unsupported fields"
            )
        body = deepcopy(record)
        supplied = body.pop("rehearsal_record_id")
        if supplied != digest(body):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor-binding-authorization-package-readiness-rehearsal record semantic identity changed"
            )
        bound = context["bound_upstream_identity"]
        expected = {
            "schema_version": EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION,
            "record_version": EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_RECORD_VERSION,
            "record_kind": "production-integration-execution-executor-binding-authorization-package-readiness-rehearsal-record",
            "decision": "complete_synthetic_executor_binding_authorization_package_readiness_rehearsal",
            "approved": True,
            "scope": "execution_executor_binding_authorization_package_readiness_rehearsal_only",
            "synthetic_only": True,
            "noop": True,
            "non_live": True,
            "bound_upstream_identity": deepcopy(bound),
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
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
            "executor_binding_authorization_package_readiness_rehearsal_manifest_id": manifest["manifest_id"],
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
            if record.get(key) != value:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"executor-binding-authorization-package-readiness-rehearsal record binding changed: {key}"
                )
        return {
            "rehearsal_record_id": supplied,
            "rehearsal_record_digest": digest(record),
        }, None

    def _policy_manifest_record(
        self, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        policy = self._read_json_fixture("executor-binding-authorization-package-readiness-rehearsal-policy.json")
        manifest = self._read_json_fixture("executor-binding-authorization-package-readiness-rehearsal-manifest.json")
        record = self._read_json_fixture(
            "executor-binding-authorization-package-readiness-rehearsal-record.json", optional=True
        )
        assert policy is not None and manifest is not None
        self._validate_policy_manifest(policy, manifest)
        return policy, manifest, record

    def _evaluate(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        record: dict[str, Any] | None,
    ) -> dict[str, Any]:
        source = context["bound_upstream_identity"][
            "executor_binding_authorization_package_readiness_preflight_classification"
        ]
        reasons = context["bound_upstream_identity"][
            "executor_binding_authorization_package_readiness_preflight_reason_codes"
        ]
        if source == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION27_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_INVALID",
                    *reasons,
                ],
                "rehearsal_binding": {
                    "rehearsal_record_id": None,
                    "rehearsal_record_digest": None,
                },
            }
        if source == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION27_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_PREFLIGHT_BLOCKED",
                    *reasons,
                ],
                "rehearsal_binding": {
                    "rehearsal_record_id": None,
                    "rehearsal_record_digest": None,
                },
            }
        bound = context["bound_upstream_identity"]
        expected_source_binding = {
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
        if manifest.get("executor_binding_authorization_package_readiness_preflight_binding") != expected_source_binding:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor-binding-authorization-package-readiness-rehearsal manifest binds a different Iteration 27 identity"
            )
        rehearsal_binding, reason = self._record_binding(record, context, manifest)
        if reason:
            return {
                "classification": "blocked",
                "classification_reason_codes": [reason],
                "rehearsal_binding": rehearsal_binding,
            }
        return {
            "classification": "executor_binding_authorization_package_readiness_rehearsal_complete",
            "classification_reason_codes": [
                "SYNTHETIC_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_COMPLETE"
            ],
            "rehearsal_binding": rehearsal_binding,
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
            "executor_binding_authorization_package_readiness_preflight_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_preflight_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_preflight_id": bound["executor_binding_authorization_package_readiness_preflight_id"],
            "bound_upstream_identity_digest": context["bound_upstream_identity_digest"],
            "executor_binding_authorization_package_readiness_rehearsal_policy_digest": digest(policy),
            "executor_binding_authorization_package_readiness_rehearsal_manifest_digest": digest(manifest),
            "rehearsal_record_digest": digest(record) if record else None,
            "rehearsal_record_id": record.get("rehearsal_record_id") if record else None,
        }

    def _new_state(self, identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION,
            "input_identity": deepcopy(identity),
            "evaluation": None,
            "attempts": {
                "evaluation": 0,
                "receipts": {},
                "artifact_assembly": 0,
            },
            "metrics": {
                "validation_checks": 0,
                "evaluation_attempts": 0,
                "evaluation_reuse": 0,
                "receipt_build_attempts": 0,
                "receipt_reuse": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "elapsed_ms": 0,
            },
            "receipt_digests": {},
        }

    def _load_state(self, identity: dict[str, Any]) -> dict[str, Any]:
        state = self.store.read_json(self.state_path)
        if state is None:
            state = self._new_state(identity)
            self.store._atomic_write(self.state_path, state)
            return state
        if (
            state.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION
            or state.get("input_identity") != identity
        ):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "executor-binding-authorization-package-readiness-rehearsal durable state binds different inputs"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION,
                "attempts": deepcopy(state["attempts"]),
                "metrics": deepcopy(state["metrics"]),
                "receipt_digests": deepcopy(state["receipt_digests"]),
            },
        )

    def _record_incident(self, boundary_id: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION,
                "boundary_id": boundary_id,
                "failure_class": self.failure_class,
                "input_identity": deepcopy(state["input_identity"]),
                "result": "pending",
            },
        )

    def _recover_incident_if_needed(self, state: dict[str, Any]) -> None:
        incident = self.store.read_json(self.incident_path)
        if incident and incident.get("result") == "pending":
            if incident.get("input_identity") != state.get("input_identity"):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor-binding-authorization-package-readiness-rehearsal incident binds different inputs"
                )
            incident["result"] = "recovered"
            self.store._atomic_write(self.incident_path, incident)

    def _receipt_path(self, position: int) -> Path:
        return self.store.run_dir / f"executor-binding-authorization-package-readiness-rehearsal-receipt-{position:02d}.json"

    def _receipt_record(
        self,
        context: dict[str, Any],
        evaluated: dict[str, Any],
        position: int,
        source: dict[str, Any],
    ) -> dict[str, Any]:
        bound = context["bound_upstream_identity"]
        body = {
            "schema_version": EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION,
            "receipt_version": EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_RECEIPT_VERSION,
            "executor_binding_authorization_package_readiness_preflight_id": bound["executor_binding_authorization_package_readiness_preflight_id"],
            "executor_binding_authorization_package_readiness_preflight_artifact_digest": bound[
                "executor_binding_authorization_package_readiness_preflight_artifact_digest"
            ],
            "executor_binding_authorization_package_readiness_rehearsal_record_id": evaluated[
                "rehearsal_binding"
            ]["rehearsal_record_id"],
            "synthetic_binding_plan_descriptor_id": bound[
                "synthetic_binding_plan_descriptor_id"
            ],
            "synthetic_binding_plan_descriptor_digest": bound[
                "synthetic_binding_plan_descriptor_digest"
            ],
            "position": position,
            "source_executor_binding_authorization_package_readiness_preflight_evidence_id": source["receipt_id"],
            "source_executor_binding_authorization_package_readiness_preflight_evidence_digest": digest(source),
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
        if evaluated["classification"] != "executor_binding_authorization_package_readiness_rehearsal_complete":
            return []
        sources = context["source_executor_binding_authorization_package_readiness_preflight_evidence"]
        if len(sources) != 10:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "complete executor-binding rehearsal requires ten source validations"
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
                    raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                        f"cached executor-binding-authorization-package-readiness-rehearsal receipt changed at position {position}"
                    )
                state["metrics"]["receipt_reuse"] += 1
                state["receipt_digests"][key] = digest(existing)
                receipts.append(existing)
                continue
            if final_locked is not None and final_locked.get("status") == "locked":
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"locked rehearsal artifact is missing receipt at position {position}"
                )
            state["attempts"]["receipts"][key] += 1
            state["metrics"]["receipt_build_attempts"] += 1
            self._save_state(state)
            boundary = f"validation:{position}"
            if self.failure_boundary_id == boundary and not self._failure_fired:
                self._failure_fired = True
                self._record_incident(boundary, state)
                self._write_metrics(state)
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure(
                    "executor_binding_authorization_package_readiness_rehearsal_evidence_validation",
                    boundary,
                    self.failure_class,
                )
            self.store._atomic_write(path, expected)
            state["receipt_digests"][key] = digest(expected)
            self._save_state(state)
            receipts.append(expected)
        if len(receipts) != 10:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "complete executor-binding rehearsal must produce exactly ten receipts"
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
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure(
                    "executor_binding_authorization_package_readiness_rehearsal_evaluation",
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
                "executor_binding_authorization_package_readiness_rehearsal_policy_id": policy["policy_id"],
                "executor_binding_authorization_package_readiness_rehearsal_policy_version": policy[
                    "executor_binding_authorization_package_readiness_rehearsal_policy_version"
                ],
                "executor_binding_authorization_package_readiness_rehearsal_manifest_id": manifest["manifest_id"],
                "evidence": deepcopy(manifest["evidence"]),
            }
            self._save_state(state)
        else:
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        receipts = self._ensure_receipts(context, evaluated, state)
        evaluated["executor_binding_authorization_package_readiness_rehearsal_receipts"] = receipts
        state["metrics"]["elapsed_ms"] = max(
            0, int((time.monotonic() - started) * 1000)
        )
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
        return evaluated

    def _artifact_data(self, evaluated: dict[str, Any]) -> dict[str, Any]:
        rehearsal_binding = evaluated["rehearsal_binding"]
        receipts = evaluated["executor_binding_authorization_package_readiness_rehearsal_receipts"]
        evidence = evaluated["evidence"]
        if evaluated["classification"] == "executor_binding_authorization_package_readiness_rehearsal_complete":
            if len(receipts) != 10:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor_binding_authorization_package_readiness_rehearsal_complete requires ten no-op receipts"
                )
            if len({x["receipt_id"] for x in receipts}) != 10:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor-binding-authorization-package-readiness-rehearsal receipt identities must be unique"
                )
        elif receipts:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "blocked or invalid rehearsal cannot carry receipts"
            )
        identity = {
            "executor_binding_authorization_package_readiness_rehearsal_schema_version": (
                EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_SCHEMA_VERSION
            ),
            "executor_binding_authorization_package_readiness_rehearsal_policy_version": evaluated[
                "executor_binding_authorization_package_readiness_rehearsal_policy_version"
            ],
            "executor_binding_authorization_package_readiness_rehearsal_policy_id": evaluated[
                "executor_binding_authorization_package_readiness_rehearsal_policy_id"
            ],
            "executor_binding_authorization_package_readiness_rehearsal_policy_digest": evaluated[
                "input_identity"
            ]["executor_binding_authorization_package_readiness_rehearsal_policy_digest"],
            "executor_binding_authorization_package_readiness_rehearsal_manifest_id": evaluated[
                "executor_binding_authorization_package_readiness_rehearsal_manifest_id"
            ],
            "executor_binding_authorization_package_readiness_rehearsal_manifest_digest": evaluated[
                "input_identity"
            ]["executor_binding_authorization_package_readiness_rehearsal_manifest_digest"],
            "separate_executor_binding_authorization_package_readiness_rehearsal_id": rehearsal_binding[
                "rehearsal_record_id"
            ],
            "separate_executor_binding_authorization_package_readiness_rehearsal_digest": rehearsal_binding[
                "rehearsal_record_digest"
            ],
            **deepcopy(evaluated["bound_upstream_identity"]),
            "bound_upstream_identity_digest": evaluated[
                "bound_upstream_identity_digest"
            ],
            "executor_binding_authorization_package_readiness_rehearsal_receipt_ids": [
                x["receipt_id"] for x in receipts
            ],
            "executor_binding_authorization_package_readiness_rehearsal_receipt_digests": [
                digest(x) for x in receipts
            ],
            "executor_binding_authorization_package_readiness_rehearsal_receipt_set_digest": digest(receipts),
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
            "executor_binding_authorization_package_readiness_rehearsal_id": digest(identity),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": (
                "synthetic_shadow_execution_executor_binding_authorization_package_readiness_rehearsal_only"
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
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure(
                "executor_binding_authorization_package_readiness_rehearsal_validation",
                "executor_binding_authorization_package_readiness_rehearsal_artifact",
                "cached executor-binding-authorization-package-readiness-rehearsal artifact invalid",
            )
        if existing.get("data") != self._artifact_data(evaluated):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure(
                "executor_binding_authorization_package_readiness_rehearsal_validation",
                "executor_binding_authorization_package_readiness_rehearsal_artifact",
                "cached executor-binding-authorization-package-readiness-rehearsal artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_executor_binding_authorization_package_readiness_rehearsal(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id == "final_executor_binding_authorization_package_readiness_rehearsal_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._record_incident(
                "final_executor_binding_authorization_package_readiness_rehearsal_artifact", state
            )
            self._write_metrics(state)
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalBoundaryFailure(
                "executor_binding_authorization_package_readiness_rehearsal_artifact_assembly",
                "final_executor_binding_authorization_package_readiness_rehearsal_artifact",
                self.failure_class,
            )
        return self._artifact_data(evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "final executor-binding-authorization-package-readiness-rehearsal artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "final executor-binding-authorization-package-readiness-rehearsal artifact digest invalid"
            )
        data = artifact.get("data") or {}
        self._assert_no_authority(data, "Iteration 28 artifact")
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
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    f"executor-binding rehearsal cannot perform {flag}"
                )
        classification = data.get("classification")
        if classification == "executor_binding_authorization_package_readiness_rehearsal_complete":
            if (
                data.get("executor_binding_authorization_package_readiness_preflight_classification")
                != "executor_binding_authorization_package_readiness_preflight_complete"
            ):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor_binding_authorization_package_readiness_rehearsal_complete requires qualified Iteration 27 preflight"
                )
            if not data.get("separate_executor_binding_authorization_package_readiness_rehearsal_id"):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor_binding_authorization_package_readiness_rehearsal_complete requires separate rehearsal record"
                )
            ids = list(data.get("executor_binding_authorization_package_readiness_rehearsal_receipt_ids") or [])
            digests = list(data.get("executor_binding_authorization_package_readiness_rehearsal_receipt_digests") or [])
            if len(ids) != 10 or len(digests) != 10:
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor_binding_authorization_package_readiness_rehearsal_complete requires ten receipts"
                )
            if len(ids) != len(set(ids)) or len(digests) != len(set(digests)):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor-binding-authorization-package-readiness-rehearsal receipt inventory contains duplicates"
                )
            loaded = []
            for position, (expected_id, expected_digest) in enumerate(
                zip(ids, digests), start=1
            ):
                receipt = self.store.read_json(self._receipt_path(position))
                if receipt is None:
                    raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                        f"executor-binding-authorization-package-readiness-rehearsal receipt missing at position {position}"
                    )
                if (
                    receipt.get("receipt_id") != expected_id
                    or digest(receipt) != expected_digest
                    or receipt.get("position") != position
                    or receipt.get("receipt_version")
                    != EXECUTION_EXECUTOR_BINDING_AUTHORIZATION_PACKAGE_READINESS_REHEARSAL_RECEIPT_VERSION
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
                    raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                        f"unsafe or corrupted executor-binding-authorization-package-readiness-rehearsal receipt at position {position}"
                    )
                loaded.append(receipt)
            if digest(loaded) != data.get(
                "executor_binding_authorization_package_readiness_rehearsal_receipt_set_digest"
            ):
                raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                    "executor-binding-authorization-package-readiness-rehearsal receipt set digest changed"
                )
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionExecutorBindingAuthorizationPackageReadinessRehearsalError(
                "unsupported executor-binding-authorization-package-readiness-rehearsal classification"
            )
