from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    EXECUTION_EXECUTOR_BINDING_READINESS_POLICY_VERSION,
    EXECUTION_EXECUTOR_BINDING_READINESS_SCHEMA_VERSION,
    EXECUTION_EXECUTOR_BINDING_PREFLIGHT_POLICY_VERSION,
    EXECUTION_EXECUTOR_BINDING_PREFLIGHT_RECORD_VERSION,
    EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION,
    EXECUTION_EXECUTOR_BINDING_PLAN_DESCRIPTOR_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest


class IntegrationExecutionExecutorBindingPreflightError(ContractError):
    pass


class IntegrationExecutionExecutorBindingPreflightBoundaryFailure(
    IntegrationExecutionExecutorBindingPreflightError
):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id


class ProductionIntegrationExecutionExecutorBindingPreflight:
    """Deterministic synthetic-only Iteration 21 executor-binding preflight gate."""

    ARTIFACT_TYPE = "production-integration-execution-executor-binding-preflight"
    SOURCE_ARTIFACT_TYPE = "production-integration-execution-executor-binding-readiness"

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
        "executor_binding_readiness_id",
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

    TRANSITIVE_FIELDS = ()

    POLICY_KEYS = {
        "schema_version",
        "executor_binding_preflight_policy_version",
        "policy_id",
        "synthetic_only",
        "allowed_upstream_classification",
        "classifications",
        "real_executor_binding_permitted",
        "real_authority_permitted",
        "zero_incremental_cost_required",
    }

    MANIFEST_KEYS = {
        "schema_version",
        "executor_binding_preflight_manifest_version",
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
        "executor_binding_readiness_binding",
        "binding_plan_descriptor_binding",
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

    DESCRIPTOR_KEYS = {
        "schema_version",
        "descriptor_version",
        "descriptor_kind",
        "descriptor_id",
        "synthetic_only",
        "non_live",
        "plan_kind",
        "bound_synthetic_executor_descriptor_id",
        "bound_synthetic_executor_descriptor_digest",
        "external_endpoint",
        "service_url",
        "account",
        "environment",
        "credential_reference",
        "secret_reference",
        "token_reference",
        "deployment_target",
        "schedule_reference",
        "production_resource",
        "invocation_capability",
        "real_executor_binding_capability",
        "executable_command",
        "executable_steps",
        "network_side_effect",
        "production_write_capability",
        "paid_dependency_required",
        "authority_scope",
        "production_authority_granted",
        "external_mutation_permitted",
    }

    RECORD_KEYS = {
        "schema_version",
        "record_version",
        "record_kind",
        "preflight_record_id",
        "decision",
        "approved",
        "scope",
        "synthetic_only",
        "executor_binding_readiness_artifact_digest",
        "executor_binding_readiness_id",
        "executor_binding_readiness_policy_id",
        "executor_binding_readiness_policy_digest",
        "executor_binding_readiness_manifest_id",
        "executor_binding_readiness_manifest_digest",
        "separate_executor_binding_readiness_id",
        "separate_executor_binding_readiness_digest",
        "synthetic_executor_descriptor_id",
        "synthetic_executor_descriptor_digest",
        "executor_binding_provenance_validation_set_digest",
        "canonical_chain_digest",
        "bound_upstream_identity_digest",
        "synthetic_binding_plan_descriptor_id",
        "synthetic_binding_plan_descriptor_digest",
        "executor_binding_preflight_manifest_id",
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
        failure_class: str = "synthetic_integration_execution_executor_binding_preflight_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = fixture_root
        self.failure_boundary_id = (
            failure_boundary_id.removeprefix("executor_binding_preflight:")
            if failure_boundary_id
            else None
        )
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "executor-binding-preflight-state.json"
        self.metrics_path = self.store.run_dir / "executor-binding-preflight-metrics.json"
        self.incident_path = self.store.run_dir / "executor-binding-preflight-incident.json"

    def _read_json_fixture(
        self, name: str, *, optional: bool = False
    ) -> dict[str, Any] | None:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "production executor-binding preflight is intentionally unconfigured"
            )
        path = self.fixture_root / name
        if not path.exists():
            if optional:
                return None
            raise IntegrationExecutionExecutorBindingPreflightError(
                f"executor-binding-preflight fixture missing: {name}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _locked(self, artifact_type: str) -> dict[str, Any]:
        artifact = self.store.load_artifact(artifact_type)
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionExecutorBindingPreflightError(
                f"locked artifact missing: {artifact_type}"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionExecutorBindingPreflightError(
                f"locked artifact corrupted: {artifact_type}"
            )
        return artifact

    def _assert_no_authority(self, record: dict[str, Any], label: str) -> None:
        for flag in (*self.AUTHORITY_FLAGS, *self.MUTATION_FLAGS):
            if record.get(flag) is not False:
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"{label} must keep {flag}=false"
                )
        if record.get("real_integration_steps_enabled", 0) != 0:
            raise IntegrationExecutionExecutorBindingPreflightError(
                f"{label} cannot enable real integration steps"
            )
        if record.get("real_integration_steps_executed", 0) != 0:
            raise IntegrationExecutionExecutorBindingPreflightError(
                f"{label} cannot execute real integration steps"
            )

    def _source_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            key: deepcopy(value)
            for key, value in data.items()
            if key not in self.SOURCE_OUTPUT_FIELDS
        }

    def _source_validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"executor-binding-readiness-validation-{position:02d}.json"

    def _load_source_validations(
        self, data: dict[str, Any]
    ) -> list[dict[str, Any]]:
        ids = list(data.get("executor_binding_provenance_validation_ids") or [])
        digests = list(data.get("executor_binding_provenance_validation_digests") or [])
        if len(ids) != len(digests):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 executor-binding provenance inventory length mismatch"
            )
        if len(ids) != len(set(ids)) or len(digests) != len(set(digests)):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 executor-binding provenance inventory contains duplicates"
            )
        classification = data.get("classification")
        if classification == "executor_binding_ready" and len(ids) != 10:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor_binding_ready requires ten Iteration 20 provenance validations"
            )
        if classification != "executor_binding_ready" and ids:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "non-ready Iteration 20 input cannot carry executor-binding provenance validations"
            )
        validations: list[dict[str, Any]] = []
        for position, (expected_id, expected_digest) in enumerate(
            zip(ids, digests), start=1
        ):
            record = self.store.read_json(self._source_validation_path(position))
            if record is None:
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"Iteration 20 provenance validation missing at position {position}"
                )
            if record.get("validation_id") != expected_id or digest(record) != expected_digest:
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"Iteration 20 provenance validation changed at position {position}"
                )
            if (
                record.get("position") != position
                or record.get("noop_verified") is not True
                or record.get("side_effect_free_verified") is not True
                or record.get("real_executor_binding_performed") is not False
                or record.get("external_mutation_performed") is not False
            ):
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"Iteration 20 provenance validation unsafe at position {position}"
                )
            validations.append(record)
        return validations

    def _bound_upstream_identity(
        self,
        artifact: dict[str, Any],
        data: dict[str, Any],
        validations: list[dict[str, Any]],
    ) -> dict[str, Any]:
        semantic_identity = self._source_identity(data)
        return {
            "executor_binding_readiness_artifact_digest": artifact["content_digest"],
            "executor_binding_readiness_id": data["executor_binding_readiness_id"],
            "executor_binding_readiness_classification": data["classification"],
            "executor_binding_readiness_reason_codes": deepcopy(
                data.get("classification_reason_codes") or []
            ),
            "executor_binding_readiness_policy_id": data.get(
                "executor_binding_readiness_policy_id"
            ),
            "executor_binding_readiness_policy_digest": data.get(
                "executor_binding_readiness_policy_digest"
            ),
            "executor_binding_readiness_manifest_id": data.get(
                "executor_binding_readiness_manifest_id"
            ),
            "executor_binding_readiness_manifest_digest": data.get(
                "executor_binding_readiness_manifest_digest"
            ),
            "separate_executor_binding_readiness_id": data.get(
                "separate_executor_binding_readiness_id"
            ),
            "separate_executor_binding_readiness_digest": data.get(
                "separate_executor_binding_readiness_digest"
            ),
            "synthetic_executor_descriptor_id": data.get(
                "synthetic_executor_descriptor_id"
            ),
            "synthetic_executor_descriptor_digest": data.get(
                "synthetic_executor_descriptor_digest"
            ),
            "executor_binding_provenance_validation_ids": deepcopy(
                data.get("executor_binding_provenance_validation_ids") or []
            ),
            "executor_binding_provenance_validation_digests": deepcopy(
                data.get("executor_binding_provenance_validation_digests") or []
            ),
            "executor_binding_provenance_validation_set_digest": digest(validations),
            "canonical_chain_digest": data.get("canonical_chain_digest"),
            "iteration20_semantic_identity": semantic_identity,
            "iteration20_semantic_identity_digest": digest(semantic_identity),
        }

    def _context(self, run: dict[str, Any]) -> dict[str, Any]:
        if (
            run.get("current_state") != "Complete"
            or run.get("completion_status") != "complete_locked"
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding preflight requires Complete / complete_locked"
            )
        artifact = self._locked(self.SOURCE_ARTIFACT_TYPE)
        data = artifact.get("data") or {}
        if data.get("executor_binding_readiness_schema_version") != (
            EXECUTION_EXECUTOR_BINDING_READINESS_SCHEMA_VERSION
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "unsupported Iteration 20 executor-binding-readiness schema version"
            )
        if data.get("executor_binding_readiness_policy_version") != (
            EXECUTION_EXECUTOR_BINDING_READINESS_POLICY_VERSION
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "unsupported Iteration 20 executor-binding-readiness policy version"
            )
        expected_id = digest(self._source_identity(data))
        if data.get("executor_binding_readiness_id") != expected_id:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 executor_binding_readiness_id does not match semantic identity"
            )
        self._assert_no_authority(data, "Iteration 20 executor-binding-readiness artifact")
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
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"Iteration 20 executor-binding-readiness artifact must keep {flag}=false"
                )
        if data.get("synthetic_only") is not True:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 executor-binding-readiness artifact must be synthetic-only"
            )
        if any(item.get("enabled") is not False for item in data.get("execution_steps") or []):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 executor-binding-readiness artifact contains an executable step"
            )
        if data.get("executor_binding_readiness_policy_id") != (
            "production-integration-execution-executor-binding-readiness-v1"
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 policy identity changed"
            )
        if data.get("executor_binding_readiness_manifest_id") != (
            "production-integration-execution-executor-binding-readiness-manifest-v1"
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 manifest identity changed"
            )
        classification = data.get("classification")
        if classification not in {"blocked", "executor_binding_ready", "invalid"}:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "unsupported Iteration 20 classification"
            )
        if classification == "executor_binding_ready":
            if not data.get("separate_executor_binding_readiness_id"):
                raise IntegrationExecutionExecutorBindingPreflightError(
                    "executor_binding_ready requires separate Iteration 20 readiness identity"
                )
            if not data.get("synthetic_executor_descriptor_id"):
                raise IntegrationExecutionExecutorBindingPreflightError(
                    "executor_binding_ready requires Iteration 20 synthetic executor descriptor identity"
                )
        source_state = self.store.read_json(
            self.store.run_dir / "executor-binding-readiness-state.json"
        )
        source_evaluation = (source_state or {}).get("evaluation") or {}
        source_input_identity = source_evaluation.get("input_identity") or {}
        source_readiness_binding = source_evaluation.get("readiness_binding") or {}
        source_descriptor_binding = source_evaluation.get("descriptor_binding") or {}
        if (
            source_evaluation.get("classification") != data.get("classification")
            or source_evaluation.get("classification_reason_codes")
            != data.get("classification_reason_codes")
            or source_evaluation.get("executor_binding_readiness_policy_id")
            != data.get("executor_binding_readiness_policy_id")
            or source_evaluation.get("executor_binding_readiness_manifest_id")
            != data.get("executor_binding_readiness_manifest_id")
            or source_input_identity.get("executor_binding_readiness_policy_digest")
            != data.get("executor_binding_readiness_policy_digest")
            or source_input_identity.get("executor_binding_readiness_manifest_digest")
            != data.get("executor_binding_readiness_manifest_digest")
            or source_readiness_binding.get("readiness_record_id")
            != data.get("separate_executor_binding_readiness_id")
            or source_readiness_binding.get("readiness_record_digest")
            != data.get("separate_executor_binding_readiness_digest")
            or source_descriptor_binding.get("synthetic_executor_descriptor_id")
            != data.get("synthetic_executor_descriptor_id")
            or source_descriptor_binding.get("synthetic_executor_descriptor_digest")
            != data.get("synthetic_executor_descriptor_digest")
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 20 durable executor-binding-readiness provenance does not match locked artifact"
            )
        validations = self._load_source_validations(data)
        bound = self._bound_upstream_identity(artifact, data, validations)
        return {
            "executor_binding_readiness_artifact": artifact,
            "executor_binding_readiness_data": data,
            "source_executor_binding_validations": validations,
            "bound_upstream_identity": bound,
            "bound_upstream_identity_digest": digest(bound),
        }

    def _validate_policy_manifest(
        self,
        policy: dict[str, Any],
        manifest: dict[str, Any],
    ) -> None:
        if set(policy) != self.POLICY_KEYS:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 21 policy contains unsupported fields"
            )
        if set(manifest) != self.MANIFEST_KEYS:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 21 manifest contains unsupported fields"
            )
        if (
            policy.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION
            or policy.get("executor_binding_preflight_policy_version")
            != EXECUTION_EXECUTOR_BINDING_PREFLIGHT_POLICY_VERSION
            or policy.get("policy_id")
            != "production-integration-execution-executor-binding-preflight-v1"
            or policy.get("synthetic_only") is not True
            or policy.get("allowed_upstream_classification")
            != "executor_binding_ready"
            or policy.get("classifications")
            != ["blocked", "executor_binding_preflight_qualified", "invalid"]
            or policy.get("real_executor_binding_permitted") is not False
            or policy.get("real_authority_permitted") is not False
            or policy.get("zero_incremental_cost_required") is not True
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "unsupported or unsafe Iteration 21 executor-binding-preflight policy"
            )
        if (
            manifest.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION
            or manifest.get("executor_binding_preflight_manifest_version") != "1.0.0"
            or manifest.get("manifest_id")
            != "production-integration-execution-executor-binding-preflight-manifest-v1"
            or manifest.get("synthetic_only") is not True
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "unsupported Iteration 21 executor-binding-preflight manifest"
            )
        self._assert_no_authority(manifest, "Iteration 21 manifest")
        evidence = manifest.get("evidence") or {}
        if set(evidence) != self.EVIDENCE_KEYS:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "Iteration 21 manifest evidence contains unsupported fields"
            )
        executor = evidence.get("executor_declaration") or {}
        credential = evidence.get("credential_declaration") or {}
        target = evidence.get("target_declaration") or {}
        rollback = evidence.get("rollback_declaration") or {}
        cost = evidence.get("cost_declaration") or {}
        if executor != {
            "real_executor_required": False,
            "real_executor_present": False,
            "real_executor_bound": False,
            "real_executor_invocable": False,
            "real_executor_invocation_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor declaration is not synthetic-only"
            )
        if credential != {
            "production_credentials_required": False,
            "production_credentials_present": False,
            "production_credentials_stored": False,
            "credentials_use_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "credential declaration is not fail-closed"
            )
        if target != {
            "scope": "synthetic_non_production",
            "real_target_present": False,
            "real_target_contacted": False,
            "real_target_contact_authorized": False,
        }:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "target declaration is not fail-closed"
            )
        if rollback != {
            "rollback_plan_bound": True,
            "rollback_execution_authorized": False,
            "rollback_executed": False,
        }:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "rollback declaration is not fail-closed"
            )
        if cost != {
            "incremental_paid_dependency_required": False,
            "zero_incremental_cost_approved": True,
        }:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "zero-incremental-cost approval missing"
            )
        required_stops = {
            "identity_mismatch",
            "authority_flag_true",
            "cost_guard_failed",
            "provenance_validation_mismatch",
            "preflight_record_missing",
            "binding_plan_descriptor_missing",
            "binding_plan_descriptor_unsafe",
            "real_executor_binding_capability_present",
            "executable_command_present",
            "executable_step_present",
        }
        if set(evidence.get("stop_abort_conditions") or []) != required_stops:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding-preflight stop/abort conditions incomplete"
            )

    def _descriptor_binding(
        self, descriptor: dict[str, Any] | None, context: dict[str, Any]
    ) -> dict[str, Any]:
        if descriptor is None:
            return {
                "synthetic_binding_plan_descriptor_id": None,
                "synthetic_binding_plan_descriptor_digest": None,
            }
        if set(descriptor) != self.DESCRIPTOR_KEYS:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "synthetic binding-plan descriptor contains unsupported fields"
            )
        bound = context["bound_upstream_identity"]
        if (
            descriptor.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION
            or descriptor.get("descriptor_version")
            != EXECUTION_EXECUTOR_BINDING_PLAN_DESCRIPTOR_VERSION
            or descriptor.get("descriptor_kind") != "synthetic-binding-plan-descriptor"
            or descriptor.get("synthetic_only") is not True
            or descriptor.get("non_live") is not True
            or descriptor.get("plan_kind") != "synthetic_noop_binding_plan"
            or descriptor.get("bound_synthetic_executor_descriptor_id")
            != bound.get("synthetic_executor_descriptor_id")
            or descriptor.get("bound_synthetic_executor_descriptor_digest")
            != bound.get("synthetic_executor_descriptor_digest")
            or descriptor.get("authority_scope")
            != "iteration21_logical_preflight_testing_only"
            or descriptor.get("invocation_capability") is not False
            or descriptor.get("real_executor_binding_capability") is not False
            or descriptor.get("executable_command") is not None
            or descriptor.get("executable_steps") != []
            or descriptor.get("network_side_effect") is not False
            or descriptor.get("production_write_capability") is not False
            or descriptor.get("paid_dependency_required") is not False
            or descriptor.get("production_authority_granted") is not False
            or descriptor.get("external_mutation_permitted") is not False
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "unsafe or unsupported synthetic binding-plan descriptor"
            )
        for key in (
            "external_endpoint",
            "service_url",
            "account",
            "environment",
            "credential_reference",
            "secret_reference",
            "token_reference",
            "deployment_target",
            "schedule_reference",
            "production_resource",
        ):
            if descriptor.get(key) is not None:
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"synthetic binding-plan descriptor cannot identify real resource: {key}"
                )
        body = deepcopy(descriptor)
        supplied = body.pop("descriptor_id")
        expected = digest(body)
        if supplied != expected:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "synthetic binding-plan descriptor semantic identity changed"
            )
        return {
            "synthetic_binding_plan_descriptor_id": supplied,
            "synthetic_binding_plan_descriptor_digest": digest(descriptor),
        }

    def _record_binding(
        self,
        record: dict[str, Any] | None,
        context: dict[str, Any],
        manifest: dict[str, Any],
        descriptor_binding: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None]:
        if record is None:
            return {
                "preflight_record_id": None,
                "preflight_record_digest": None,
            }, "EXECUTOR_BINDING_PREFLIGHT_RECORD_MISSING"
        if set(record) != self.RECORD_KEYS:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding-preflight record contains unsupported fields"
            )
        body = deepcopy(record)
        supplied = body.pop("preflight_record_id")
        if supplied != digest(body):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding-preflight record semantic identity changed"
            )
        bound = context["bound_upstream_identity"]
        expected = {
            "schema_version": EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION,
            "record_version": EXECUTION_EXECUTOR_BINDING_PREFLIGHT_RECORD_VERSION,
            "record_kind": "production-integration-execution-executor-binding-preflight-record",
            "decision": "qualify_synthetic_executor_binding_preflight",
            "approved": True,
            "scope": "execution_executor_binding_preflight_only",
            "synthetic_only": True,
            "executor_binding_readiness_artifact_digest": bound[
                "executor_binding_readiness_artifact_digest"
            ],
            "executor_binding_readiness_id": bound[
                "executor_binding_readiness_id"
            ],
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
            "synthetic_binding_plan_descriptor_id": descriptor_binding[
                "synthetic_binding_plan_descriptor_id"
            ],
            "synthetic_binding_plan_descriptor_digest": descriptor_binding[
                "synthetic_binding_plan_descriptor_digest"
            ],
            "executor_binding_preflight_manifest_id": manifest["manifest_id"],
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
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"executor-binding-preflight record binding changed: {key}"
                )
        return {
            "preflight_record_id": supplied,
            "preflight_record_digest": digest(record),
        }, None

    def _policy_manifest_record_descriptor(
        self, context: dict[str, Any]
    ) -> tuple[
        dict[str, Any],
        dict[str, Any],
        dict[str, Any] | None,
        dict[str, Any] | None,
    ]:
        policy = self._read_json_fixture("executor-binding-preflight-policy.json")
        manifest = self._read_json_fixture("executor-binding-preflight-manifest.json")
        record = self._read_json_fixture(
            "executor-binding-preflight-record.json", optional=True
        )
        descriptor = self._read_json_fixture(
            "synthetic-binding-plan-descriptor.json", optional=True
        )
        assert policy is not None and manifest is not None
        self._validate_policy_manifest(policy, manifest)
        return policy, manifest, record, descriptor

    def _evaluate(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        record: dict[str, Any] | None,
        descriptor: dict[str, Any] | None,
    ) -> dict[str, Any]:
        source_classification = context["bound_upstream_identity"][
            "executor_binding_readiness_classification"
        ]
        source_reasons = context["bound_upstream_identity"][
            "executor_binding_readiness_reason_codes"
        ]
        if source_classification == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION20_EXECUTOR_BINDING_READINESS_INVALID",
                    *source_reasons,
                ],
                "descriptor_binding": {
                    "synthetic_binding_plan_descriptor_id": None,
                    "synthetic_binding_plan_descriptor_digest": None,
                },
                "preflight_binding": {
                    "preflight_record_id": None,
                    "preflight_record_digest": None,
                },
            }
        if source_classification == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION20_EXECUTOR_BINDING_READINESS_BLOCKED",
                    *source_reasons,
                ],
                "descriptor_binding": {
                    "synthetic_binding_plan_descriptor_id": None,
                    "synthetic_binding_plan_descriptor_digest": None,
                },
                "preflight_binding": {
                    "preflight_record_id": None,
                    "preflight_record_digest": None,
                },
            }
        if descriptor is None:
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "SYNTHETIC_BINDING_PLAN_DESCRIPTOR_MISSING"
                ],
                "descriptor_binding": {
                    "synthetic_binding_plan_descriptor_id": None,
                    "synthetic_binding_plan_descriptor_digest": None,
                },
                "preflight_binding": {
                    "preflight_record_id": None,
                    "preflight_record_digest": None,
                },
            }
        descriptor_binding = self._descriptor_binding(descriptor, context)
        bound = context["bound_upstream_identity"]
        expected_source_binding = {
            "binding_mode": "exact_locked_executor_binding_readiness_artifact",
            "executor_binding_readiness_artifact_digest": bound[
                "executor_binding_readiness_artifact_digest"
            ],
            "executor_binding_readiness_id": bound[
                "executor_binding_readiness_id"
            ],
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
            "bound_upstream_identity_digest": context[
                "bound_upstream_identity_digest"
            ],
        }
        if manifest.get("executor_binding_readiness_binding") != expected_source_binding:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding-preflight manifest binds a different Iteration 20 identity"
            )
        expected_descriptor_binding = {
            "binding_mode": "exact_non_live_synthetic_binding_plan_descriptor",
            **descriptor_binding,
        }
        if manifest.get("binding_plan_descriptor_binding") != expected_descriptor_binding:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding-preflight manifest binds a different synthetic binding plan"
            )
        preflight_binding, reason = self._record_binding(
            record, context, manifest, descriptor_binding
        )
        if reason:
            return {
                "classification": "blocked",
                "classification_reason_codes": [reason],
                "descriptor_binding": descriptor_binding,
                "preflight_binding": preflight_binding,
            }
        return {
            "classification": "executor_binding_preflight_qualified",
            "classification_reason_codes": [
                "SYNTHETIC_EXECUTOR_BINDING_PREFLIGHT_QUALIFIED"
            ],
            "descriptor_binding": descriptor_binding,
            "preflight_binding": preflight_binding,
        }

    def _input_identity(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        record: dict[str, Any] | None,
        descriptor: dict[str, Any] | None,
    ) -> dict[str, Any]:
        bound = context["bound_upstream_identity"]
        return {
            "executor_binding_readiness_artifact_digest": bound[
                "executor_binding_readiness_artifact_digest"
            ],
            "executor_binding_readiness_id": bound[
                "executor_binding_readiness_id"
            ],
            "bound_upstream_identity_digest": context[
                "bound_upstream_identity_digest"
            ],
            "executor_binding_preflight_policy_digest": digest(policy),
            "executor_binding_preflight_manifest_digest": digest(manifest),
            "preflight_record_digest": (
                digest(record) if record else None
            ),
            "preflight_record_id": (
                record.get("preflight_record_id") if record else None
            ),
            "synthetic_binding_plan_descriptor_digest": (
                digest(descriptor) if descriptor else None
            ),
            "synthetic_binding_plan_descriptor_id": (
                descriptor.get("descriptor_id") if descriptor else None
            ),
        }

    def _new_state(self, identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION,
            "input_identity": deepcopy(identity),
            "evaluation": None,
            "attempts": {
                "evaluation": 0,
                "validations": {},
                "artifact_assembly": 0,
            },
            "metrics": {
                "validation_checks": 0,
                "evaluation_attempts": 0,
                "evaluation_reuse": 0,
                "provenance_validation_attempts": 0,
                "provenance_validation_reuse": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "elapsed_ms": 0,
            },
            "validation_digests": {},
        }

    def _load_state(self, identity: dict[str, Any]) -> dict[str, Any]:
        state = self.store.read_json(self.state_path)
        if state is None:
            state = self._new_state(identity)
            self.store._atomic_write(self.state_path, state)
            return state
        if (
            state.get("schema_version")
            != EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION
            or state.get("input_identity") != identity
        ):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding-preflight durable state binds different inputs"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION,
                "attempts": deepcopy(state["attempts"]),
                "metrics": deepcopy(state["metrics"]),
                "validation_digests": deepcopy(state["validation_digests"]),
            },
        )

    def _record_incident(self, boundary_id: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION,
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
                raise IntegrationExecutionExecutorBindingPreflightError(
                    "executor-binding-preflight incident binds different inputs"
                )
            incident["result"] = "recovered"
            self.store._atomic_write(self.incident_path, incident)

    def _validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"executor-binding-preflight-validation-{position:02d}.json"

    def _validation_record(
        self,
        context: dict[str, Any],
        position: int,
        source: dict[str, Any],
        descriptor_id: str,
    ) -> dict[str, Any]:
        body = {
            "schema_version": EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION,
            "executor_binding_readiness_id": context[
                "bound_upstream_identity"
            ]["executor_binding_readiness_id"],
            "position": position,
            "source_executor_binding_validation_id": source["validation_id"],
            "source_executor_binding_validation_digest": digest(source),
            "synthetic_binding_plan_descriptor_id": descriptor_id,
            "noop_verified": source.get("noop_verified"),
            "side_effect_free_verified": source.get("side_effect_free_verified"),
            "real_executor_binding_performed": False,
            "real_executor_invocation_performed": False,
            "external_mutation_performed": False,
        }
        return {**body, "validation_id": digest(body)}

    def _ensure_provenance_validations(
        self,
        context: dict[str, Any],
        evaluated: dict[str, Any],
        state: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if evaluated["classification"] != "executor_binding_preflight_qualified":
            return []
        descriptor_id = evaluated["descriptor_binding"][
            "synthetic_binding_plan_descriptor_id"
        ]
        result: list[dict[str, Any]] = []
        for position, source in enumerate(
            context["source_executor_binding_validations"], start=1
        ):
            expected = self._validation_record(
                context, position, source, descriptor_id
            )
            path = self._validation_path(position)
            existing = self.store.read_json(path)
            key = str(position)
            state["attempts"]["validations"].setdefault(key, 0)
            if existing is not None:
                if existing != expected:
                    raise IntegrationExecutionExecutorBindingPreflightError(
                        f"cached executor-binding-preflight provenance validation changed at position {position}"
                    )
                state["metrics"]["provenance_validation_reuse"] += 1
                state["validation_digests"][key] = digest(existing)
                result.append(existing)
                continue
            state["attempts"]["validations"][key] += 1
            state["metrics"]["provenance_validation_attempts"] += 1
            self._save_state(state)
            boundary = f"validation:{position}"
            if self.failure_boundary_id == boundary and not self._failure_fired:
                self._failure_fired = True
                self._record_incident(boundary, state)
                self._write_metrics(state)
                raise IntegrationExecutionExecutorBindingPreflightBoundaryFailure(
                    "executor_binding_preflight_provenance_validation",
                    boundary,
                    self.failure_class,
                )
            self.store._atomic_write(path, expected)
            state["validation_digests"][key] = digest(expected)
            self._save_state(state)
            result.append(expected)
        return result

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        context = self._context(run)
        policy, manifest, record, descriptor = (
            self._policy_manifest_record_descriptor(context)
        )
        identity = self._input_identity(
            context, policy, manifest, record, descriptor
        )
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
                raise IntegrationExecutionExecutorBindingPreflightBoundaryFailure(
                    "executor_binding_preflight_evaluation",
                    "evaluation",
                    self.failure_class,
                )
            outcome = self._evaluate(
                context, policy, manifest, record, descriptor
            )
            state["evaluation"] = {
                **outcome,
                "input_identity": deepcopy(identity),
                "bound_upstream_identity": deepcopy(
                    context["bound_upstream_identity"]
                ),
                "bound_upstream_identity_digest": context[
                    "bound_upstream_identity_digest"
                ],
                "executor_binding_preflight_policy_id": policy["policy_id"],
                "executor_binding_preflight_policy_version": policy[
                    "executor_binding_preflight_policy_version"
                ],
                "executor_binding_preflight_manifest_id": manifest[
                    "manifest_id"
                ],
                "synthetic_binding_plan_descriptor": deepcopy(descriptor),
                "evidence": deepcopy(manifest["evidence"]),
            }
            self._save_state(state)
        else:
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        validations = self._ensure_provenance_validations(
            context, evaluated, state
        )
        evaluated["executor_binding_preflight_provenance_validations"] = validations
        state["metrics"]["elapsed_ms"] = max(
            0, int((time.monotonic() - started) * 1000)
        )
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
        return evaluated

    def _artifact_data(self, evaluated: dict[str, Any]) -> dict[str, Any]:
        preflight_binding = evaluated["preflight_binding"]
        descriptor_binding = evaluated["descriptor_binding"]
        evidence = evaluated["evidence"]
        identity = {
            "executor_binding_preflight_schema_version": (
                EXECUTION_EXECUTOR_BINDING_PREFLIGHT_SCHEMA_VERSION
            ),
            "executor_binding_preflight_policy_version": evaluated[
                "executor_binding_preflight_policy_version"
            ],
            "executor_binding_preflight_policy_id": evaluated[
                "executor_binding_preflight_policy_id"
            ],
            "executor_binding_preflight_policy_digest": evaluated[
                "input_identity"
            ]["executor_binding_preflight_policy_digest"],
            "executor_binding_preflight_manifest_id": evaluated[
                "executor_binding_preflight_manifest_id"
            ],
            "executor_binding_preflight_manifest_digest": evaluated[
                "input_identity"
            ]["executor_binding_preflight_manifest_digest"],
            "separate_executor_binding_preflight_id": preflight_binding[
                "preflight_record_id"
            ],
            "separate_executor_binding_preflight_digest": preflight_binding[
                "preflight_record_digest"
            ],
            "synthetic_binding_plan_descriptor_id": descriptor_binding[
                "synthetic_binding_plan_descriptor_id"
            ],
            "synthetic_binding_plan_descriptor_digest": descriptor_binding[
                "synthetic_binding_plan_descriptor_digest"
            ],
            "synthetic_binding_plan_descriptor": deepcopy(
                evaluated["synthetic_binding_plan_descriptor"]
            ),
            **deepcopy(evaluated["bound_upstream_identity"]),
            "bound_upstream_identity_digest": evaluated[
                "bound_upstream_identity_digest"
            ],
            "executor_binding_preflight_provenance_validation_ids": [
                x["validation_id"]
                for x in evaluated["executor_binding_preflight_provenance_validations"]
            ],
            "executor_binding_preflight_provenance_validation_digests": [
                digest(x)
                for x in evaluated["executor_binding_preflight_provenance_validations"]
            ],
            "executor_declaration": deepcopy(evidence["executor_declaration"]),
            "credential_declaration": deepcopy(
                evidence["credential_declaration"]
            ),
            "target_declaration": deepcopy(evidence["target_declaration"]),
            "rollback_declaration": deepcopy(evidence["rollback_declaration"]),
            "stop_abort_conditions": deepcopy(
                evidence["stop_abort_conditions"]
            ),
            "cost_declaration": deepcopy(evidence["cost_declaration"]),
            "classification": evaluated["classification"],
            "classification_reason_codes": deepcopy(
                evaluated["classification_reason_codes"]
            ),
        }
        return {
            **identity,
            "executor_binding_preflight_id": digest(identity),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": (
                "synthetic_shadow_execution_executor_binding_preflight_only"
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
            raise IntegrationExecutionExecutorBindingPreflightBoundaryFailure(
                "executor_binding_preflight_validation",
                "executor_binding_preflight_artifact",
                "cached executor-binding-preflight artifact invalid",
            )
        if existing.get("data") != self._artifact_data(evaluated):
            raise IntegrationExecutionExecutorBindingPreflightBoundaryFailure(
                "executor_binding_preflight_validation",
                "executor_binding_preflight_artifact",
                "cached executor-binding-preflight artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_executor_binding_preflight(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id
            == "final_executor_binding_preflight_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._record_incident(
                "final_executor_binding_preflight_artifact", state
            )
            self._write_metrics(state)
            raise IntegrationExecutionExecutorBindingPreflightBoundaryFailure(
                "executor_binding_preflight_artifact_assembly",
                "final_executor_binding_preflight_artifact",
                self.failure_class,
            )
        return self._artifact_data(evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionExecutorBindingPreflightError(
                "final executor-binding-preflight artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "final executor-binding-preflight artifact digest invalid"
            )
        data = artifact.get("data") or {}
        self._assert_no_authority(data, "Iteration 21 artifact")
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
                raise IntegrationExecutionExecutorBindingPreflightError(
                    f"executor-binding preflight cannot perform {flag}"
                )
        if any(item.get("enabled") is not False for item in data.get("execution_steps") or []):
            raise IntegrationExecutionExecutorBindingPreflightError(
                "executor-binding preflight cannot enable a real executable step"
            )
        classification = data.get("classification")
        if classification == "executor_binding_preflight_qualified":
            if data.get("executor_binding_readiness_classification") != "executor_binding_ready":
                raise IntegrationExecutionExecutorBindingPreflightError(
                    "executor_binding_preflight_qualified requires executor_binding_ready upstream"
                )
            if not data.get("separate_executor_binding_preflight_id"):
                raise IntegrationExecutionExecutorBindingPreflightError(
                    "executor_binding_preflight_qualified requires separate preflight record"
                )
            descriptor = data.get("synthetic_binding_plan_descriptor") or {}
            if (
                descriptor.get("plan_kind") != "synthetic_noop_binding_plan"
                or descriptor.get("invocation_capability") is not False
                or descriptor.get("real_executor_binding_capability") is not False
                or descriptor.get("executable_command") is not None
                or descriptor.get("executable_steps") != []
            ):
                raise IntegrationExecutionExecutorBindingPreflightError(
                    "executor_binding_preflight_qualified requires non-live no-op binding plan"
                )
            if len(data.get("executor_binding_preflight_provenance_validation_ids") or []) != 10:
                raise IntegrationExecutionExecutorBindingPreflightError(
                    "executor_binding_preflight_qualified requires ten provenance validations"
                )
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionExecutorBindingPreflightError(
                "unsupported executor-binding-preflight classification"
            )
