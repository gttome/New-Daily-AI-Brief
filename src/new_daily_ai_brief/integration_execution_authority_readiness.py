from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    EXECUTION_AUTHORIZATION_PACKAGE_POLICY_VERSION,
    EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION,
    EXECUTION_AUTHORITY_READINESS_POLICY_VERSION,
    EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest


class IntegrationExecutionAuthorityReadinessError(ContractError):
    pass


class IntegrationExecutionAuthorityReadinessBoundaryFailure(
    IntegrationExecutionAuthorityReadinessError
):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id


class ProductionIntegrationExecutionAuthorityReadiness:
    """Deterministic synthetic-only Iteration 19 execution-authority readiness gate."""

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

    PACKAGE_OUTPUT_FIELDS = {
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

    TRANSITIVE_FIELDS = (
        "authorization_decision_artifact_digest",
        "authorization_decision_id",
        "authorization_decision_classification",
        "authorization_decision_reason_codes",
        "authorization_decision_policy_id",
        "authorization_decision_policy_digest",
        "authorization_decision_manifest_id",
        "authorization_decision_manifest_digest",
        "separate_authorization_decision_id",
        "separate_authorization_decision_digest",
        "authorization_review_artifact_digest",
        "authorization_review_id",
        "authorization_review_classification",
        "authorization_review_reason_codes",
        "authorization_review_policy_id",
        "authorization_review_policy_digest",
        "authorization_review_manifest_id",
        "authorization_review_manifest_digest",
        "authorization_review_decision_id",
        "authorization_review_decision_digest",
        "review_receipt_verification_ids",
        "review_receipt_verification_digests",
        "review_receipt_verification_set_digest",
        "execution_rehearsal_artifact_digest",
        "execution_rehearsal_id",
        "execution_attempt_id",
        "rehearsal_policy_id",
        "rehearsal_policy_digest",
        "rehearsal_manifest_id",
        "rehearsal_manifest_digest",
        "rehearsal_decision_id",
        "rehearsal_decision_digest",
        "rehearsal_receipt_ids",
        "rehearsal_receipt_set_digest",
        "execution_preflight_artifact_digest",
        "execution_preflight_id",
        "admission_artifact_digest",
        "admission_id",
        "plan_artifact_digest",
        "plan_id",
        "plan_graph_digest",
        "dry_run_assertion_set_digest",
        "rollback_boundary_set_digest",
        "preflight_artifact_digest",
        "preflight_id",
        "readiness_artifact_digest",
        "readiness_assessment_id",
        "completion_artifact_digest",
        "final_completion_receipt_digest",
        "canonical_chain_digest",
        "execution_steps",
    )

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_integration_execution_authority_readiness_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = fixture_root
        self.failure_boundary_id = (
            failure_boundary_id.removeprefix("authority_readiness:")
            if failure_boundary_id
            else None
        )
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "authority-readiness-state.json"
        self.metrics_path = self.store.run_dir / "authority-readiness-metrics.json"
        self.incident_path = self.store.run_dir / "authority-readiness-incident.json"

    def _read_json_fixture(self, name: str, *, optional: bool = False) -> dict[str, Any] | None:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionAuthorityReadinessError(
                "production execution-authority readiness is intentionally unconfigured"
            )
        path = self.fixture_root / name
        if not path.exists():
            if optional:
                return None
            raise IntegrationExecutionAuthorityReadinessError(
                f"authority-readiness fixture missing: {name}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _assert_authority_false(self, record: dict[str, Any], label: str) -> None:
        for flag in self.AUTHORITY_FLAGS:
            if record.get(flag) is not False:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"{label} must keep {flag}=false"
                )
        if record.get("real_integration_steps_enabled", 0) != 0:
            raise IntegrationExecutionAuthorityReadinessError(
                f"{label} cannot enable real integration steps"
            )

    def _locked(self, artifact_type: str) -> dict[str, Any]:
        artifact = self.store.load_artifact(artifact_type)
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionAuthorityReadinessError(
                f"locked artifact missing: {artifact_type}"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionAuthorityReadinessError(
                f"locked artifact corrupted: {artifact_type}"
            )
        return artifact

    def _package_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        return {
            key: deepcopy(value)
            for key, value in data.items()
            if key not in self.PACKAGE_OUTPUT_FIELDS
        }

    def _source_validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"authorization-decision-verification-{position:02d}.json"

    def _package_validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"authorization-package-validation-{position:02d}.json"

    def _load_validation_inventory(
        self,
        data: dict[str, Any],
        *,
        prefix: str,
        path_factory,
        id_field: str,
        digest_field: str,
    ) -> list[dict[str, Any]]:
        ids = deepcopy(data.get(id_field) or [])
        digests = deepcopy(data.get(digest_field) or [])
        if data.get("classification") != "authorization_package_ready":
            if ids or digests:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"blocked/invalid Iteration 18 cannot carry {prefix} validations"
                )
            return []
        if len(ids) != 10 or len(digests) != 10 or len(set(ids)) != 10:
            raise IntegrationExecutionAuthorityReadinessError(
                f"authorization_package_ready requires ten unique {prefix} validations"
            )
        records: list[dict[str, Any]] = []
        for position in range(1, 11):
            record = self.store.read_json(path_factory(position))
            if not record:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"{prefix} validation missing at position {position}"
                )
            if record.get("validation_id") != ids[position - 1]:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"{prefix} validation order/id changed"
                )
            if digest(record) != digests[position - 1]:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"{prefix} validation digest changed"
                )
            if (
                record.get("position") != position
                or record.get("noop_verified") is not True
                or record.get("side_effect_free_verified") is not True
            ):
                raise IntegrationExecutionAuthorityReadinessError(
                    f"{prefix} validation is unsafe"
                )
            records.append(record)
        return records

    def _context(self, run: dict[str, Any]) -> dict[str, Any]:
        if (
            run.get("current_state") != "Complete"
            or run.get("completion_status") != "complete_locked"
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "integration_execution_authority_readiness_only requires Complete / complete_locked"
            )

        package = self._locked("production-integration-execution-authorization-package")
        pd = package.get("data") or {}
        if (
            pd.get("authorization_package_schema_version")
            != EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION
            or pd.get("authorization_package_policy_version")
            != EXECUTION_AUTHORIZATION_PACKAGE_POLICY_VERSION
            or pd.get("authorization_package_policy_id")
            != "production-integration-execution-authorization-package-v1"
            or pd.get("authorization_package_manifest_id")
            != "production-integration-execution-authorization-package-manifest-v1"
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "Iteration 18 authorization-package identity/version unsupported"
            )
        if digest(self._package_identity(pd)) != pd.get("authorization_package_id"):
            raise IntegrationExecutionAuthorityReadinessError(
                "Iteration 18 authorization-package identity is corrupted"
            )
        if (
            pd.get("final_state") != "Complete"
            or pd.get("final_status") != "complete_locked"
            or pd.get("completion_scope")
            != "synthetic_shadow_execution_authorization_package_only"
            or pd.get("synthetic_only") is not True
            or pd.get("real_integration_steps_enabled") != 0
            or pd.get("real_integration_steps_executed") != 0
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "Iteration 18 authorization-package semantics are stale"
            )
        self._assert_authority_false(pd, "Iteration 18 authorization-package")
        if any(x.get("enabled") is not False for x in pd.get("execution_steps") or []):
            raise IntegrationExecutionAuthorityReadinessError(
                "Iteration 18 real integration steps must remain disabled"
            )

        package_state = self.store.read_json(
            self.store.run_dir / "authorization-package-state.json"
        )
        if not package_state or package_state.get("schema_version") != EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION:
            raise IntegrationExecutionAuthorityReadinessError(
                "Iteration 18 durable package state missing or unsupported"
            )
        package_input = package_state.get("input_identity") or {}
        for actual, expected, label in (
            (pd.get("authorization_package_policy_digest"), package_input.get("authorization_package_policy_digest"), "package policy digest"),
            (pd.get("authorization_package_manifest_digest"), package_input.get("authorization_package_manifest_digest"), "package manifest digest"),
            (pd.get("separate_authorization_package_id"), package_input.get("authorization_package_record_id"), "separate package id"),
            (pd.get("separate_authorization_package_digest"), package_input.get("authorization_package_record_digest"), "separate package digest"),
            (pd.get("authorization_decision_artifact_digest"), package_input.get("authorization_decision_artifact_digest"), "decision artifact digest"),
            (pd.get("authorization_decision_id"), package_input.get("authorization_decision_id"), "decision id"),
        ):
            if actual != expected:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"Iteration 18 {label} changed"
                )

        decision = self._locked("production-integration-execution-authorization-decision")
        review = self._locked("production-integration-execution-authorization-review")
        rehearsal = self._locked("production-integration-execution-rehearsal")
        execution_preflight = self._locked("production-integration-execution-preflight")
        admission = self._locked("production-integration-admission")
        plan = self._locked("production-integration-plan")
        preflight = self._locked("production-integration-preflight")
        readiness = self._locked("readiness-admission")
        completion = self._locked("completion")
        dd = decision.get("data") or {}

        checks = (
            (pd.get("authorization_decision_artifact_digest"), decision["content_digest"], "decision digest"),
            (pd.get("authorization_decision_id"), dd.get("authorization_decision_id"), "decision id"),
            (pd.get("authorization_decision_policy_id"), dd.get("authorization_decision_policy_id"), "decision policy id"),
            (pd.get("authorization_decision_policy_digest"), dd.get("authorization_decision_policy_digest"), "decision policy digest"),
            (pd.get("authorization_decision_manifest_id"), dd.get("authorization_decision_manifest_id"), "decision manifest id"),
            (pd.get("authorization_decision_manifest_digest"), dd.get("authorization_decision_manifest_digest"), "decision manifest digest"),
            (pd.get("separate_authorization_decision_id"), dd.get("separate_authorization_decision_id"), "separate decision id"),
            (pd.get("separate_authorization_decision_digest"), dd.get("separate_authorization_decision_digest"), "separate decision digest"),
            (pd.get("authorization_review_artifact_digest"), review["content_digest"], "review digest"),
            (pd.get("authorization_review_id"), review["data"].get("authorization_review_id"), "review id"),
            (pd.get("execution_rehearsal_artifact_digest"), rehearsal["content_digest"], "rehearsal digest"),
            (pd.get("execution_rehearsal_id"), rehearsal["data"].get("execution_rehearsal_id"), "rehearsal id"),
            (pd.get("execution_attempt_id"), rehearsal["data"].get("execution_attempt_id"), "execution attempt id"),
            (pd.get("execution_preflight_artifact_digest"), execution_preflight["content_digest"], "execution preflight digest"),
            (pd.get("execution_preflight_id"), execution_preflight["data"].get("execution_preflight_id"), "execution preflight id"),
            (pd.get("admission_artifact_digest"), admission["content_digest"], "admission digest"),
            (pd.get("admission_id"), admission["data"].get("admission_id"), "admission id"),
            (pd.get("plan_artifact_digest"), plan["content_digest"], "plan digest"),
            (pd.get("plan_id"), plan["data"].get("plan_id"), "plan id"),
            (pd.get("preflight_artifact_digest"), preflight["content_digest"], "preflight digest"),
            (pd.get("preflight_id"), preflight["data"].get("preflight_id"), "preflight id"),
            (pd.get("readiness_artifact_digest"), readiness["content_digest"], "readiness digest"),
            (pd.get("readiness_assessment_id"), readiness["data"].get("assessment_id"), "readiness id"),
            (pd.get("completion_artifact_digest"), completion["content_digest"], "completion digest"),
        )
        for actual, expected, label in checks:
            if actual != expected:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"Iteration 18 transitive {label} binding changed"
                )

        for field in self.TRANSITIVE_FIELDS:
            if field in dd and pd.get(field) != dd.get(field):
                raise IntegrationExecutionAuthorityReadinessError(
                    f"Iteration 18 transitive {field} changed from Iteration 17"
                )

        plan_data = plan["data"]
        if pd.get("plan_graph_digest") != digest(plan_data.get("plan_steps") or []):
            raise IntegrationExecutionAuthorityReadinessError("Iteration 12 plan graph changed")
        if pd.get("dry_run_assertion_set_digest") != digest(
            plan_data.get("dry_run_assertion_set") or []
        ):
            raise IntegrationExecutionAuthorityReadinessError("dry-run assertion set changed")
        if pd.get("rollback_boundary_set_digest") != digest(
            plan_data.get("rollback_boundary_set") or []
        ):
            raise IntegrationExecutionAuthorityReadinessError("rollback boundary set changed")

        classification = pd.get("classification")
        if classification not in {"blocked", "authorization_package_ready", "invalid"}:
            raise IntegrationExecutionAuthorityReadinessError(
                "unsupported Iteration 18 authorization-package classification"
            )
        if classification == "authorization_package_ready" and (
            not pd.get("separate_authorization_package_id")
            or not pd.get("separate_authorization_package_digest")
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "authorization_package_ready lacks separate package identity"
            )

        source_validations = self._load_validation_inventory(
            pd,
            prefix="source provenance",
            path_factory=self._source_validation_path,
            id_field="source_provenance_validation_ids",
            digest_field="source_provenance_validation_digests",
        )
        package_validations = self._load_validation_inventory(
            pd,
            prefix="package provenance",
            path_factory=self._package_validation_path,
            id_field="package_provenance_validation_ids",
            digest_field="package_provenance_validation_digests",
        )
        if classification == "authorization_package_ready":
            if digest(source_validations) != pd.get("source_provenance_validation_set_digest"):
                raise IntegrationExecutionAuthorityReadinessError(
                    "Iteration 17 source provenance validation set changed"
                )
            for position, record in enumerate(package_validations, start=1):
                if (
                    record.get("source_validation_id")
                    != source_validations[position - 1].get("validation_id")
                    or record.get("source_validation_digest")
                    != digest(source_validations[position - 1])
                ):
                    raise IntegrationExecutionAuthorityReadinessError(
                        "Iteration 18 package provenance substitution changed"
                    )

        context = {
            "authorization_package_artifact_digest": package["content_digest"],
            "authorization_package_id": pd["authorization_package_id"],
            "authorization_package_classification": classification,
            "authorization_package_reason_codes": deepcopy(
                pd.get("classification_reason_codes") or []
            ),
            "authorization_package_policy_id": pd.get("authorization_package_policy_id"),
            "authorization_package_policy_digest": pd.get("authorization_package_policy_digest"),
            "authorization_package_manifest_id": pd.get("authorization_package_manifest_id"),
            "authorization_package_manifest_digest": pd.get("authorization_package_manifest_digest"),
            "separate_authorization_package_id": pd.get("separate_authorization_package_id"),
            "separate_authorization_package_digest": pd.get("separate_authorization_package_digest"),
            "source_provenance_validations": source_validations,
            "source_provenance_validation_ids": deepcopy(pd.get("source_provenance_validation_ids") or []),
            "source_provenance_validation_digests": deepcopy(pd.get("source_provenance_validation_digests") or []),
            "source_provenance_validation_set_digest": pd.get("source_provenance_validation_set_digest"),
            "package_provenance_validations": package_validations,
            "package_provenance_validation_ids": deepcopy(pd.get("package_provenance_validation_ids") or []),
            "package_provenance_validation_digests": deepcopy(pd.get("package_provenance_validation_digests") or []),
            "package_provenance_validation_set_digest": digest(package_validations),
        }
        for field in self.TRANSITIVE_FIELDS:
            context[field] = deepcopy(pd.get(field))
        return context

    def _policy_manifest_record(
        self, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        policy = self._read_json_fixture("authority-readiness-policy.json")
        manifest = self._read_json_fixture("authority-readiness-manifest.json")
        record = self._read_json_fixture("authority-readiness-record.json", optional=True)
        assert policy is not None and manifest is not None
        if (
            policy.get("schema_version") != EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION
            or policy.get("execution_authority_readiness_policy_version")
            != EXECUTION_AUTHORITY_READINESS_POLICY_VERSION
            or policy.get("policy_id")
            != "production-integration-execution-authority-readiness-v1"
            or policy.get("synthetic_only") is not True
            or policy.get("real_authority_permitted") is not False
            or policy.get("zero_incremental_cost_required") is not True
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "execution-authority-readiness policy unsupported"
            )
        if (
            manifest.get("schema_version") != EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION
            or manifest.get("execution_authority_readiness_manifest_version") != "1.0.0"
            or manifest.get("manifest_id")
            != "production-integration-execution-authority-readiness-manifest-v1"
            or manifest.get("synthetic_only") is not True
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "execution-authority-readiness manifest unsupported"
            )
        self._assert_authority_false(manifest, "authority-readiness manifest")
        evidence = manifest.get("evidence") or {}
        required = (
            "executor_declaration",
            "credential_declaration",
            "target_declaration",
            "rollback_declaration",
            "stop_abort_conditions",
            "authority_state",
            "cost_declaration",
        )
        if any(key not in evidence for key in required):
            raise IntegrationExecutionAuthorityReadinessError(
                "authority-readiness evidence envelope incomplete"
            )
        if evidence["executor_declaration"] != {
            "real_executor_required": False,
            "real_executor_present": False,
            "real_executor_bound": False,
            "real_executor_invocation_authorized": False,
        }:
            raise IntegrationExecutionAuthorityReadinessError("executor declaration unsafe")
        if evidence["credential_declaration"] != {
            "credentials_required": False,
            "credentials_present": False,
            "credentials_stored": False,
            "credentials_use_authorized": False,
        }:
            raise IntegrationExecutionAuthorityReadinessError("credential declaration unsafe")
        if evidence["target_declaration"] != {
            "scope": "synthetic_non_production",
            "real_target_present": False,
            "real_target_contacted": False,
            "real_target_contact_authorized": False,
        }:
            raise IntegrationExecutionAuthorityReadinessError("target declaration unsafe")
        if evidence["rollback_declaration"] != {
            "rollback_plan_bound": True,
            "rollback_execution_authorized": False,
        }:
            raise IntegrationExecutionAuthorityReadinessError("rollback declaration unsafe")
        if evidence["cost_declaration"] != {
            "incremental_paid_dependency_required": False,
            "zero_incremental_cost_approved": True,
        }:
            raise IntegrationExecutionAuthorityReadinessError(
                "zero-incremental-cost declaration missing"
            )
        expected_abort = {
            "identity_mismatch",
            "authority_flag_true",
            "cost_guard_failed",
            "provenance_validation_mismatch",
            "readiness_record_missing",
        }
        if set(evidence["stop_abort_conditions"]) != expected_abort:
            raise IntegrationExecutionAuthorityReadinessError(
                "stop/abort conditions incomplete"
            )
        self._assert_authority_false(evidence["authority_state"], "authority state")
        return policy, manifest, record

    def _record_id(self, record: dict[str, Any]) -> str:
        body = deepcopy(record)
        body.pop("readiness_record_id", None)
        return digest(body)

    def _record_binding(
        self,
        record: dict[str, Any] | None,
        context: dict[str, Any],
        manifest: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None]:
        if record is None:
            return {
                "readiness_record_id": None,
                "readiness_record_digest": None,
            }, "EXECUTION_AUTHORITY_READINESS_RECORD_MISSING"
        if (
            record.get("schema_version") != EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION
            or record.get("readiness_record_version") != "1.0.0"
            or record.get("record_kind")
            != "production-integration-execution-authority-readiness-record"
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "execution-authority-readiness record version unsupported"
            )
        if record.get("readiness_record_id") != self._record_id(record):
            raise IntegrationExecutionAuthorityReadinessError(
                "execution-authority-readiness record identity changed"
            )
        self._assert_authority_false(record, "authority-readiness record")
        expected = {
            "authorization_package_artifact_digest": context["authorization_package_artifact_digest"],
            "authorization_package_id": context["authorization_package_id"],
            "authorization_package_policy_id": context["authorization_package_policy_id"],
            "authorization_package_policy_digest": context["authorization_package_policy_digest"],
            "authorization_package_manifest_id": context["authorization_package_manifest_id"],
            "authorization_package_manifest_digest": context["authorization_package_manifest_digest"],
            "separate_authorization_package_id": context["separate_authorization_package_id"],
            "separate_authorization_package_digest": context["separate_authorization_package_digest"],
            "source_provenance_validation_set_digest": context["source_provenance_validation_set_digest"],
            "package_provenance_validation_set_digest": context["package_provenance_validation_set_digest"],
            "authorization_decision_artifact_digest": context["authorization_decision_artifact_digest"],
            "authorization_decision_id": context["authorization_decision_id"],
            "authorization_review_artifact_digest": context["authorization_review_artifact_digest"],
            "authorization_review_id": context["authorization_review_id"],
            "execution_rehearsal_artifact_digest": context["execution_rehearsal_artifact_digest"],
            "execution_rehearsal_id": context["execution_rehearsal_id"],
            "execution_attempt_id": context["execution_attempt_id"],
            "execution_preflight_id": context["execution_preflight_id"],
            "admission_id": context["admission_id"],
            "plan_id": context["plan_id"],
            "plan_graph_digest": context["plan_graph_digest"],
            "dry_run_assertion_set_digest": context["dry_run_assertion_set_digest"],
            "rollback_boundary_set_digest": context["rollback_boundary_set_digest"],
            "preflight_id": context["preflight_id"],
            "readiness_assessment_id": context["readiness_assessment_id"],
            "final_completion_receipt_digest": context["final_completion_receipt_digest"],
            "canonical_chain_digest": context["canonical_chain_digest"],
            "authority_readiness_manifest_id": manifest["manifest_id"],
        }
        for key, value in expected.items():
            if record.get(key) != value:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"execution-authority-readiness record binding changed: {key}"
                )
        if (
            record.get("synthetic_only") is not True
            or record.get("approved") is not True
            or record.get("decision")
            != "admit_synthetic_execution_authority_readiness_boundary"
            or record.get("scope") != "execution_authority_readiness_only"
            or record.get("grants_production_authority") is not False
            or record.get("grants_executor_invocation_authority") is not False
            or record.get("grants_credential_use_authority") is not False
            or record.get("grants_real_target_contact_authority") is not False
            or record.get("grants_rollback_execution_authority") is not False
            or record.get("grants_cutover_authority") is not False
            or record.get("grants_decommission_authority") is not False
            or record.get("grants_publication_authority") is not False
            or record.get("external_mutation_permitted") is not False
            or record.get("zero_incremental_cost_approved") is not True
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "execution-authority-readiness record grants unsafe authority"
            )
        return {
            "readiness_record_id": record["readiness_record_id"],
            "readiness_record_digest": digest(record),
        }, None

    def _evaluate(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        record: dict[str, Any] | None,
    ) -> dict[str, Any]:
        classification = context["authorization_package_classification"]
        if classification == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION18_AUTHORIZATION_PACKAGE_INVALID",
                    *context["authorization_package_reason_codes"],
                ],
                "readiness_binding": {
                    "readiness_record_id": None,
                    "readiness_record_digest": None,
                },
            }
        if classification == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION18_AUTHORIZATION_PACKAGE_BLOCKED",
                    *context["authorization_package_reason_codes"],
                ],
                "readiness_binding": {
                    "readiness_record_id": None,
                    "readiness_record_digest": None,
                },
            }

        binding = manifest.get("authorization_package_binding") or {}
        expected = {
            "binding_mode": "exact_locked_authorization_package_artifact",
            "authorization_package_artifact_digest": context["authorization_package_artifact_digest"],
            "authorization_package_id": context["authorization_package_id"],
            "authorization_package_policy_id": context["authorization_package_policy_id"],
            "authorization_package_policy_digest": context["authorization_package_policy_digest"],
            "authorization_package_manifest_id": context["authorization_package_manifest_id"],
            "authorization_package_manifest_digest": context["authorization_package_manifest_digest"],
            "separate_authorization_package_id": context["separate_authorization_package_id"],
            "separate_authorization_package_digest": context["separate_authorization_package_digest"],
            "source_provenance_validation_ids": context["source_provenance_validation_ids"],
            "source_provenance_validation_digests": context["source_provenance_validation_digests"],
            "source_provenance_validation_set_digest": context["source_provenance_validation_set_digest"],
            "package_provenance_validation_ids": context["package_provenance_validation_ids"],
            "package_provenance_validation_digests": context["package_provenance_validation_digests"],
            "package_provenance_validation_set_digest": context["package_provenance_validation_set_digest"],
        }
        if binding != expected:
            raise IntegrationExecutionAuthorityReadinessError(
                "authority-readiness manifest binds a different Iteration 18 identity"
            )

        readiness_binding, reason = self._record_binding(record, context, manifest)
        if reason:
            return {
                "classification": "blocked",
                "classification_reason_codes": [reason],
                "readiness_binding": readiness_binding,
            }
        return {
            "classification": "execution_authority_ready",
            "classification_reason_codes": ["SYNTHETIC_EXECUTION_AUTHORITY_READY"],
            "readiness_binding": readiness_binding,
        }

    def _input_identity(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        record: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "authorization_package_artifact_digest": context[
                "authorization_package_artifact_digest"
            ],
            "authorization_package_id": context["authorization_package_id"],
            "execution_authority_readiness_policy_digest": digest(policy),
            "execution_authority_readiness_manifest_digest": digest(manifest),
            "execution_authority_readiness_record_digest": digest(record) if record else None,
            "execution_authority_readiness_record_id": (
                record.get("readiness_record_id") if record else None
            ),
        }

    def _new_state(self, identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": deepcopy(identity),
            "attempts": {"evaluation": 0, "artifact_assembly": 0, "validations": {}},
            "evaluation": None,
            "validation_digests": {},
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
        }

    def _load_state(
        self, identity: dict[str, Any] | None = None, *, optional: bool = False
    ) -> dict[str, Any] | None:
        state = self.store.read_json(self.state_path)
        if state is None:
            if optional:
                return None
            if identity is None:
                raise IntegrationExecutionAuthorityReadinessError(
                    "authority-readiness state missing"
                )
            return self._new_state(identity)
        if (
            state.get("schema_version") != EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "authority-readiness durable state version changed"
            )
        if identity is not None and state.get("input_identity") != identity:
            raise IntegrationExecutionAuthorityReadinessError(
                "authority-readiness durable state binds different inputs"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                **deepcopy(state["metrics"]),
                "attempts": deepcopy(state["attempts"]),
            },
        )

    def _record_incident(self, boundary_id: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                "boundary_id": boundary_id,
                "failure_class": self.failure_class,
                "result": "pending_recovery",
                "input_identity": deepcopy(state["input_identity"]),
            },
        )

    def _recover_incident_if_needed(self, state: dict[str, Any]) -> None:
        incident = self.store.read_json(self.incident_path)
        if not incident or incident.get("result") != "pending_recovery":
            return
        if incident.get("input_identity") != state.get("input_identity"):
            raise IntegrationExecutionAuthorityReadinessError(
                "authority-readiness incident binds different inputs"
            )
        incident["result"] = "recovered"
        self.store._atomic_write(self.incident_path, incident)

    def _validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"authority-readiness-validation-{position:02d}.json"

    def _validation_record(
        self, context: dict[str, Any], position: int, source: dict[str, Any]
    ) -> dict[str, Any]:
        body = {
            "schema_version": EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION,
            "authorization_package_id": context["authorization_package_id"],
            "position": position,
            "package_validation_id": source["validation_id"],
            "package_validation_digest": digest(source),
            "noop_verified": source.get("noop_verified"),
            "side_effect_free_verified": source.get("side_effect_free_verified"),
        }
        return {**body, "validation_id": digest(body)}

    def _ensure_provenance_validations(
        self, context: dict[str, Any], evaluated: dict[str, Any], state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if evaluated["classification"] != "execution_authority_ready":
            return []
        result: list[dict[str, Any]] = []
        for position, source in enumerate(
            context["package_provenance_validations"], start=1
        ):
            expected = self._validation_record(context, position, source)
            path = self._validation_path(position)
            existing = self.store.read_json(path)
            key = str(position)
            state["attempts"]["validations"].setdefault(key, 0)
            if existing is not None:
                if existing != expected:
                    raise IntegrationExecutionAuthorityReadinessError(
                        f"cached authority-readiness provenance validation changed at position {position}"
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
                raise IntegrationExecutionAuthorityReadinessBoundaryFailure(
                    "authority_readiness_provenance_validation",
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
        policy, manifest, record = self._policy_manifest_record(context)
        identity = self._input_identity(context, policy, manifest, record)
        state = self._load_state(identity)
        assert state is not None
        state["metrics"]["validation_checks"] += 1
        if state.get("evaluation") is None:
            state["attempts"]["evaluation"] += 1
            state["metrics"]["evaluation_attempts"] += 1
            self._save_state(state)
            if self.failure_boundary_id == "evaluation" and not self._failure_fired:
                self._failure_fired = True
                self._record_incident("evaluation", state)
                self._write_metrics(state)
                raise IntegrationExecutionAuthorityReadinessBoundaryFailure(
                    "authority_readiness_evaluation",
                    "evaluation",
                    self.failure_class,
                )
            outcome = self._evaluate(context, policy, manifest, record)
            state["evaluation"] = {
                **deepcopy(context),
                **outcome,
                "input_identity": deepcopy(identity),
                "execution_authority_readiness_policy_id": policy["policy_id"],
                "execution_authority_readiness_policy_version": policy[
                    "execution_authority_readiness_policy_version"
                ],
                "execution_authority_readiness_manifest_id": manifest["manifest_id"],
            }
            self._save_state(state)
        else:
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        validations = self._ensure_provenance_validations(context, evaluated, state)
        evaluated["readiness_provenance_validations"] = validations
        state["evaluation"]["readiness_provenance_validation_ids"] = [
            x["validation_id"] for x in validations
        ]
        state["metrics"]["elapsed_ms"] = max(
            0, int((time.monotonic() - started) * 1000)
        )
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
        return evaluated

    def _artifact_data(self, evaluated: dict[str, Any]) -> dict[str, Any]:
        readiness_binding = evaluated["readiness_binding"]
        identity = {
            "execution_authority_readiness_schema_version": EXECUTION_AUTHORITY_READINESS_SCHEMA_VERSION,
            "execution_authority_readiness_policy_version": evaluated[
                "execution_authority_readiness_policy_version"
            ],
            "execution_authority_readiness_policy_id": evaluated[
                "execution_authority_readiness_policy_id"
            ],
            "execution_authority_readiness_policy_digest": evaluated["input_identity"][
                "execution_authority_readiness_policy_digest"
            ],
            "execution_authority_readiness_manifest_id": evaluated[
                "execution_authority_readiness_manifest_id"
            ],
            "execution_authority_readiness_manifest_digest": evaluated["input_identity"][
                "execution_authority_readiness_manifest_digest"
            ],
            "separate_execution_authority_readiness_id": readiness_binding.get(
                "readiness_record_id"
            ),
            "separate_execution_authority_readiness_digest": readiness_binding.get(
                "readiness_record_digest"
            ),
            "authorization_package_artifact_digest": evaluated[
                "authorization_package_artifact_digest"
            ],
            "authorization_package_id": evaluated["authorization_package_id"],
            "authorization_package_classification": evaluated[
                "authorization_package_classification"
            ],
            "authorization_package_reason_codes": evaluated[
                "authorization_package_reason_codes"
            ],
            "authorization_package_policy_id": evaluated["authorization_package_policy_id"],
            "authorization_package_policy_digest": evaluated[
                "authorization_package_policy_digest"
            ],
            "authorization_package_manifest_id": evaluated[
                "authorization_package_manifest_id"
            ],
            "authorization_package_manifest_digest": evaluated[
                "authorization_package_manifest_digest"
            ],
            "separate_authorization_package_id": evaluated[
                "separate_authorization_package_id"
            ],
            "separate_authorization_package_digest": evaluated[
                "separate_authorization_package_digest"
            ],
            "source_provenance_validation_ids": evaluated[
                "source_provenance_validation_ids"
            ],
            "source_provenance_validation_digests": evaluated[
                "source_provenance_validation_digests"
            ],
            "source_provenance_validation_set_digest": evaluated[
                "source_provenance_validation_set_digest"
            ],
            "package_provenance_validation_ids": evaluated[
                "package_provenance_validation_ids"
            ],
            "package_provenance_validation_digests": evaluated[
                "package_provenance_validation_digests"
            ],
            "package_provenance_validation_set_digest": evaluated[
                "package_provenance_validation_set_digest"
            ],
            "readiness_provenance_validation_ids": [
                x["validation_id"] for x in evaluated["readiness_provenance_validations"]
            ],
            "readiness_provenance_validation_digests": [
                digest(x) for x in evaluated["readiness_provenance_validations"]
            ],
        }
        for field in self.TRANSITIVE_FIELDS:
            identity[field] = deepcopy(evaluated.get(field))
        identity["classification"] = evaluated["classification"]
        identity["classification_reason_codes"] = evaluated[
            "classification_reason_codes"
        ]
        return {
            **identity,
            "execution_authority_readiness_id": digest(identity),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_execution_authority_readiness_only",
            "synthetic_only": True,
            "production_action_authorized": False,
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "production_publication": False,
            "real_executor_invocation_authorized": False,
            "credentials_use_authorized": False,
            "real_target_contact_authorized": False,
            "rollback_execution_authorized": False,
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
            raise IntegrationExecutionAuthorityReadinessBoundaryFailure(
                "authority_readiness_validation",
                "authority_readiness_artifact",
                "cached authority-readiness artifact invalid",
            )
        if existing.get("data") != self._artifact_data(evaluated):
            raise IntegrationExecutionAuthorityReadinessBoundaryFailure(
                "authority_readiness_validation",
                "authority_readiness_artifact",
                "cached authority-readiness artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        assert state is not None
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_authority_readiness(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        assert state is not None
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id == "final_authority_readiness_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._record_incident("final_authority_readiness_artifact", state)
            self._write_metrics(state)
            raise IntegrationExecutionAuthorityReadinessBoundaryFailure(
                "authority_readiness_artifact_assembly",
                "final_authority_readiness_artifact",
                self.failure_class,
            )
        return self._artifact_data(evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionAuthorityReadinessError(
                "final authority-readiness artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionAuthorityReadinessError(
                "final authority-readiness artifact digest invalid"
            )
        data = artifact.get("data") or {}
        for flag in (
            *self.AUTHORITY_FLAGS,
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
            if data.get(flag) is not False:
                raise IntegrationExecutionAuthorityReadinessError(
                    f"authority-readiness gate cannot authorize/mutate {flag}"
                )
        if (
            data.get("real_integration_steps_enabled") != 0
            or data.get("real_integration_steps_executed") != 0
            or any(x.get("enabled") is not False for x in data.get("execution_steps") or [])
        ):
            raise IntegrationExecutionAuthorityReadinessError(
                "authority-readiness gate cannot enable/execute a real step"
            )
        classification = data.get("classification")
        if classification == "execution_authority_ready":
            if data.get("authorization_package_classification") != "authorization_package_ready":
                raise IntegrationExecutionAuthorityReadinessError(
                    "execution authority readiness requires authorization_package_ready upstream"
                )
            if not data.get("separate_execution_authority_readiness_id"):
                raise IntegrationExecutionAuthorityReadinessError(
                    "execution authority readiness requires separate readiness identity"
                )
            if len(data.get("package_provenance_validation_ids") or []) != 10:
                raise IntegrationExecutionAuthorityReadinessError(
                    "execution authority readiness requires ten package provenance validations"
                )
            if len(data.get("readiness_provenance_validation_ids") or []) != 10:
                raise IntegrationExecutionAuthorityReadinessError(
                    "execution authority readiness requires ten readiness validations"
                )
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionAuthorityReadinessError(
                "unsupported execution-authority-readiness classification"
            )
