from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_SCHEMA_VERSION,
    PLAN_POLICY_VERSION,
    PLAN_SCHEMA_VERSION,
    PREFLIGHT_POLICY_VERSION,
    PREFLIGHT_SCHEMA_VERSION,
    READINESS_POLICY_VERSION,
    READINESS_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class IntegrationAdmissionError(ContractError):
    pass


class IntegrationAdmissionBoundaryFailure(IntegrationAdmissionError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"admission:{boundary_id}"


class ProductionIntegrationAdmission:
    """Deterministic, non-mutating Iteration 13 production-integration admission gate."""

    REQUIRED_EVIDENCE = (
        "discovery_adapter",
        "publication_target",
        "public_deployment_verification",
        "private_command_center",
        "production_schedules",
        "subscriber_delivery",
        "migration_prerequisites",
        "rollback_restore",
        "zero_incremental_cost",
    )

    MISSING_REASON_CODES = {
        "discovery_adapter": "ADMISSION_DISCOVERY_ADAPTER_MISSING",
        "publication_target": "ADMISSION_PUBLICATION_TARGET_MISSING",
        "public_deployment_verification": "ADMISSION_PUBLIC_DEPLOYMENT_VERIFICATION_MISSING",
        "private_command_center": "ADMISSION_PRIVATE_COMMAND_CENTER_MISSING",
        "production_schedules": "ADMISSION_PRODUCTION_SCHEDULES_MISSING",
        "subscriber_delivery": "ADMISSION_SUBSCRIBER_DELIVERY_POLICY_MISSING",
        "migration_prerequisites": "ADMISSION_MIGRATION_PREREQUISITES_MISSING",
        "rollback_restore": "ADMISSION_ROLLBACK_RESTORE_MISSING",
        "zero_incremental_cost": "ADMISSION_ZERO_INCREMENTAL_COST_APPROVAL_MISSING",
    }

    EXPECTED_RECORD_KINDS = {
        "discovery_adapter": "production-discovery-adapter",
        "publication_target": "production-publication-path",
        "public_deployment_verification": "public-deployment-verification",
        "private_command_center": "private-command-center-integration",
        "production_schedules": "production-schedule-policy",
        "subscriber_delivery": "subscriber-delivery-policy",
        "migration_prerequisites": "legacy-migration-cutover-prerequisites",
        "rollback_restore": "rollback-recovery-policy",
        "zero_incremental_cost": "cost-policy-approval",
    }

    REQUIRED_FIELDS = {
        "discovery_adapter": ("adapter_id", "zero_incremental_cost"),
        "publication_target": ("publication_path_id", "target_id"),
        "public_deployment_verification": (
            "deployment_target_id",
            "verification_mechanism_id",
        ),
        "private_command_center": (
            "target_id",
            "projection_adapter_id",
            "privacy_boundary",
        ),
        "production_schedules": (
            "schedule_policy_id",
            "schedule_identities",
            "schedule_cadences",
        ),
        "subscriber_delivery": ("policy_id",),
        "migration_prerequisites": (
            "migration_plan_id",
            "prerequisites_approved",
            "cutover_authorized",
            "legacy_decommission_authorized",
        ),
        "rollback_restore": ("rollback_policy_id", "rollback_identity"),
        "zero_incremental_cost": (
            "approved",
            "zero_incremental_cost",
            "separately_billed_openai_api_required",
            "paid_completion_or_storage_api_required",
            "paid_deployment_or_hosting_api_required",
            "other_incremental_paid_dependency_required",
        ),
    }

    EXPLICIT_REFERENCE_FIELDS = (
        "adapter_id",
        "zero_incremental_cost",
        "publication_path_id",
        "target_id",
        "deployment_target_id",
        "verification_mechanism_id",
        "projection_adapter_id",
        "privacy_boundary",
        "schedule_policy_id",
        "schedule_identities",
        "schedule_cadences",
        "policy_id",
        "delivery_mode",
        "email_enabled",
        "text_enabled",
        "calendar_subscription_enabled",
        "migration_plan_id",
        "prerequisites_approved",
        "cutover_authorized",
        "legacy_decommission_authorized",
        "rollback_policy_id",
        "rollback_identity",
        "approved",
        "separately_billed_openai_api_required",
        "paid_completion_or_storage_api_required",
        "paid_deployment_or_hosting_api_required",
        "other_incremental_paid_dependency_required",
    )

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_integration_admission_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("admission:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration13-admission-state.json"
        self.metrics_path = self.store.run_dir / "iteration13-admission-metrics.json"
        self.incident_path = self.store.run_dir / "iteration13-admission-incident.json"
        self.final_receipt_path = self.store.run_dir / "iteration9-final-completion-receipt.json"

    def _read_json_fixture(self, name: str) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationAdmissionError(
                "production integration admission is repository-evidence-only and fail-closed: "
                "no approved production admission policy/evidence binding is configured"
            )
        path = self.fixture_root / name
        if not path.exists():
            raise IntegrationAdmissionError(f"missing Iteration 13 admission fixture: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _policy_and_manifest(self) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self._read_json_fixture("admission-policy.json")
        manifest = self._read_json_fixture("admission-manifest.json")
        if (
            policy.get("schema_version") != ADMISSION_SCHEMA_VERSION
            or policy.get("integration_admission_policy_version") != ADMISSION_POLICY_VERSION
        ):
            raise IntegrationAdmissionError("unsupported Iteration 13 admission policy/schema version")
        if policy.get("policy_id") != "production-integration-admission-v1":
            raise IntegrationAdmissionError("unsupported Iteration 13 admission policy identity")
        if policy.get("synthetic_only") is not True:
            raise IntegrationAdmissionError("Iteration 13 admission policy must remain synthetic_only")
        if policy.get("production_action_authorized") is not False:
            raise IntegrationAdmissionError("Iteration 13 admission policy cannot authorize production action")
        if policy.get("require_exact_plan_binding") is not True:
            raise IntegrationAdmissionError("admission policy must require exact locked plan binding")
        if policy.get("require_separate_admission_decision") is not True:
            raise IntegrationAdmissionError("admission policy must require a separate admission decision")
        if tuple(policy.get("required_evidence") or ()) != self.REQUIRED_EVIDENCE:
            raise IntegrationAdmissionError("admission evidence inventory is incomplete or ambiguous")
        if policy.get("classifications") != ["blocked", "authorization_ready", "invalid"]:
            raise IntegrationAdmissionError("admission classification policy is unsupported")

        if (
            manifest.get("schema_version") != ADMISSION_SCHEMA_VERSION
            or manifest.get("admission_manifest_version") != "1.0.0"
        ):
            raise IntegrationAdmissionError("unsupported Iteration 13 admission manifest version")
        if manifest.get("synthetic_only") is not True:
            raise IntegrationAdmissionError("admission manifest must remain synthetic_only")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if manifest.get(flag) is not False:
                raise IntegrationAdmissionError(f"admission manifest cannot authorize {flag}")

        closure = manifest.get("iteration12_closure") or {}
        if (
            closure.get("repository_closure_status") != "complete"
            or closure.get("iteration13_ready") is not True
            or closure.get("evidence_path")
            != "evidence/iteration12/synthetic-shadow-production-integration-plan-evidence.json"
        ):
            raise IntegrationAdmissionError("Iteration 12 operational closure is incomplete or untrusted")

        binding = manifest.get("plan_binding") or {}
        if binding != {
            "binding_type": "exact_locked_plan_artifact",
            "artifact_type": "production-integration-plan",
            "plan_id_field": "data.plan_id",
            "artifact_digest_field": "content_digest",
        }:
            raise IntegrationAdmissionError("admission manifest exact-plan binding declaration is invalid")

        evidence = manifest.get("evidence")
        if not isinstance(evidence, dict) or tuple(evidence.keys()) != self.REQUIRED_EVIDENCE:
            raise IntegrationAdmissionError("admission manifest evidence inventory is incomplete or ambiguous")
        decision = manifest.get("admission_decision")
        if decision is not None and not isinstance(decision, dict):
            raise IntegrationAdmissionError("admission decision must be an explicit repository record or null")
        return policy, manifest

    def _plan_context(self, run: dict[str, Any]) -> dict[str, Any]:
        if run.get("current_state") != "Complete" or run.get("completion_status") != "complete_locked":
            raise IntegrationAdmissionError(
                "integration_admission_only requires Complete / complete_locked"
            )

        plan = self.store.load_artifact("production-integration-plan")
        if not plan or plan.get("status") != "locked":
            raise IntegrationAdmissionError("locked Iteration 12 production-integration plan is missing")
        if semantic_digest(plan) != plan.get("content_digest"):
            raise IntegrationAdmissionError("locked Iteration 12 production-integration plan is corrupted")
        data = plan.get("data") or {}
        if (
            data.get("plan_schema_version") != PLAN_SCHEMA_VERSION
            or data.get("plan_policy_version") != PLAN_POLICY_VERSION
        ):
            raise IntegrationAdmissionError("Iteration 12 plan schema/policy version is unsupported")
        if (
            data.get("final_state") != "Complete"
            or data.get("final_status") != "complete_locked"
            or data.get("completion_scope") != "synthetic_shadow_plan_only"
            or data.get("synthetic_only") is not True
        ):
            raise IntegrationAdmissionError("Iteration 12 plan semantics are stale or unsafe")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if data.get(flag) is not False:
                raise IntegrationAdmissionError(f"Iteration 12 plan cannot authorize {flag}")

        semantic_identity = {
            "plan_schema_version": data.get("plan_schema_version"),
            "plan_policy_version": data.get("plan_policy_version"),
            "plan_policy_id": data.get("plan_policy_id"),
            "plan_policy_digest": data.get("plan_policy_digest"),
            "preflight_artifact_digest": data.get("preflight_artifact_digest"),
            "preflight_id": data.get("preflight_id"),
            "preflight_schema_version": data.get("preflight_schema_version"),
            "preflight_policy_version": data.get("preflight_policy_version"),
            "preflight_classification": data.get("preflight_classification"),
            "resolution_manifest_digest": data.get("resolution_manifest_digest"),
            "readiness_artifact_digest": data.get("readiness_artifact_digest"),
            "readiness_assessment_id": data.get("readiness_assessment_id"),
            "completion_artifact_digest": data.get("completion_artifact_digest"),
            "final_completion_receipt_digest": data.get("final_completion_receipt_digest"),
            "canonical_chain_digest": data.get("canonical_chain_digest"),
            "classification": data.get("classification"),
            "classification_reason_codes": data.get("classification_reason_codes"),
            "plan_steps": data.get("plan_steps"),
            "dry_run_assertion_set": data.get("dry_run_assertion_set"),
            "rollback_boundary_set": data.get("rollback_boundary_set"),
        }
        if digest(semantic_identity) != data.get("plan_id"):
            raise IntegrationAdmissionError("Iteration 12 plan identity is corrupted")

        classification = data.get("classification")
        if classification not in {"blocked", "planned", "invalid"}:
            raise IntegrationAdmissionError("unsupported Iteration 12 plan classification")
        steps = data.get("plan_steps") or []
        if len(steps) != 10 or len({x.get("step_id") for x in steps}) != 10:
            raise IntegrationAdmissionError("Iteration 12 plan graph identity is incomplete or ambiguous")
        if any(x.get("production_action_authorized") is not False for x in steps):
            raise IntegrationAdmissionError("Iteration 12 plan step cannot authorize production action")
        assertions = data.get("dry_run_assertion_set") or []
        rollbacks = data.get("rollback_boundary_set") or []
        if len(assertions) < 10 or len(rollbacks) != 10:
            raise IntegrationAdmissionError("Iteration 12 plan assertion/rollback identity is incomplete")

        preflight = self.store.load_artifact("production-integration-preflight")
        readiness = self.store.load_artifact("readiness-admission")
        completion = self.store.load_artifact("completion")
        for name, artifact in (
            ("production-integration-preflight", preflight),
            ("readiness-admission", readiness),
            ("completion", completion),
        ):
            if not artifact or artifact.get("status") != "locked":
                raise IntegrationAdmissionError(f"bound upstream artifact {name} is missing")
            if semantic_digest(artifact) != artifact.get("content_digest"):
                raise IntegrationAdmissionError(f"bound upstream artifact {name} is corrupted")

        preflight_data = preflight["data"]
        readiness_data = readiness["data"]
        completion_data = completion["data"]
        if (
            preflight_data.get("preflight_schema_version") != PREFLIGHT_SCHEMA_VERSION
            or preflight_data.get("preflight_policy_version") != PREFLIGHT_POLICY_VERSION
            or readiness_data.get("readiness_schema_version") != READINESS_SCHEMA_VERSION
            or readiness_data.get("readiness_policy_version") != READINESS_POLICY_VERSION
        ):
            raise IntegrationAdmissionError("bound upstream schema/policy version is unsupported")

        if plan.get("input_digests") != [preflight.get("content_digest")]:
            raise IntegrationAdmissionError("Iteration 12 plan dependency identity changed")
        if preflight.get("input_digests") != [readiness.get("content_digest")]:
            raise IntegrationAdmissionError("Iteration 11 preflight dependency identity changed")
        if readiness.get("input_digests") != [completion.get("content_digest")]:
            raise IntegrationAdmissionError("Iteration 10 readiness dependency identity changed")
        if data.get("preflight_artifact_digest") != preflight.get("content_digest"):
            raise IntegrationAdmissionError("Iteration 12 plan preflight artifact identity changed")
        if data.get("preflight_id") != preflight_data.get("preflight_id"):
            raise IntegrationAdmissionError("Iteration 12 plan preflight ID changed")
        if data.get("readiness_artifact_digest") != readiness.get("content_digest"):
            raise IntegrationAdmissionError("Iteration 12 plan readiness artifact identity changed")
        if data.get("readiness_assessment_id") != readiness_data.get("assessment_id"):
            raise IntegrationAdmissionError("Iteration 12 plan readiness assessment identity changed")
        if data.get("completion_artifact_digest") != completion.get("content_digest"):
            raise IntegrationAdmissionError("Iteration 12 plan completion artifact identity changed")

        final_receipt = self.store.read_json(self.final_receipt_path)
        if (
            not final_receipt
            or digest(final_receipt) != data.get("final_completion_receipt_digest")
            or readiness_data.get("final_completion_receipt_digest")
            != data.get("final_completion_receipt_digest")
        ):
            raise IntegrationAdmissionError("bound Iteration 9 final completion receipt identity changed")
        if not (
            data.get("canonical_chain_digest")
            == readiness_data.get("canonical_chain_digest")
            == completion_data.get("canonical_chain_digest")
        ):
            raise IntegrationAdmissionError("bound canonical-chain identity changed")

        return {
            "plan_artifact_digest": plan["content_digest"],
            "plan_id": data["plan_id"],
            "plan_schema_version": data["plan_schema_version"],
            "plan_policy_version": data["plan_policy_version"],
            "plan_policy_id": data["plan_policy_id"],
            "plan_policy_digest": data["plan_policy_digest"],
            "plan_classification": classification,
            "plan_reason_codes": deepcopy(data.get("classification_reason_codes") or []),
            "plan_graph_digest": digest(steps),
            "dry_run_assertion_set_digest": digest(assertions),
            "rollback_boundary_set_digest": digest(rollbacks),
            "preflight_artifact_digest": data["preflight_artifact_digest"],
            "preflight_id": data["preflight_id"],
            "readiness_artifact_digest": data["readiness_artifact_digest"],
            "readiness_assessment_id": data["readiness_assessment_id"],
            "completion_artifact_digest": data["completion_artifact_digest"],
            "final_completion_receipt_digest": data["final_completion_receipt_digest"],
            "canonical_chain_digest": data["canonical_chain_digest"],
        }

    def _new_state(self, input_identity: dict[str, str]) -> dict[str, Any]:
        return {
            "schema_version": ADMISSION_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": input_identity,
            "attempts": {"admission_evaluation": 0, "artifact_assembly": 0},
            "evaluation": None,
            "metrics": {
                "admission_validation_checks": 0,
                "admission_evaluation_attempts": 0,
                "admission_evaluation_reuse": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "blocked_classifications": 0,
                "authorization_ready_classifications": 0,
                "invalid_classifications": 0,
                "recovery_attempts": 0,
                "elapsed_ms": 0,
                "anti_rework": {
                    "locked_iterations_1_12_reexecution": 0,
                    "iteration12_plan_compilation_reexecution": 0,
                    "iteration12_plan_artifact_rebuild": 0,
                    "full_pipeline_restarts": 0,
                },
            },
        }

    def _load_state(
        self, input_identity: dict[str, str] | None = None, *, optional: bool = False
    ) -> dict[str, Any] | None:
        state = self.store.read_json(self.state_path)
        if state is None:
            if optional:
                return None
            if input_identity is None:
                raise IntegrationAdmissionError("admission state identity is required")
            return self._new_state(input_identity)
        if (
            state.get("schema_version") != ADMISSION_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationAdmissionError("Iteration 13 admission state is stale or schema-incompatible")
        if input_identity is not None and state.get("input_identity") != input_identity:
            raise IntegrationAdmissionError(
                "cached admission state binds different plan/policy/manifest identities"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": ADMISSION_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                **deepcopy(state["metrics"]),
                "attempts": deepcopy(state["attempts"]),
            },
        )

    def _record_incident(self, boundary_id: str, message: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": ADMISSION_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                "boundary_id": boundary_id,
                "failure_class": message,
                "input_identity": deepcopy(state["input_identity"]),
                "result": "pending_recovery",
                "created_at": utc_now(),
            },
        )

    def _recover_incident_if_needed(self, state: dict[str, Any]) -> None:
        incident = self.store.read_json(self.incident_path)
        if not incident or incident.get("result") != "pending_recovery":
            return
        if incident.get("input_identity") != state.get("input_identity"):
            raise IntegrationAdmissionError("admission recovery incident binds different input identity")
        incident["result"] = "recovered"
        incident["recovery_receipt"] = {
            "boundary_id": incident["boundary_id"],
            "input_identity": deepcopy(state["input_identity"]),
            "result": "recovered",
            "recovered_at": utc_now(),
        }
        state["metrics"]["recovery_attempts"] += 1
        self.store._atomic_write(self.incident_path, incident)

    def _explicit_references(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            key: deepcopy(record[key])
            for key in self.EXPLICIT_REFERENCE_FIELDS
            if key in record
        }

    def _validate_present_evidence(self, key: str, record: dict[str, Any]) -> str | None:
        if not record.get("record_id"):
            raise IntegrationAdmissionError(f"{key} admission evidence has no record_id")
        if record.get("record_kind") != self.EXPECTED_RECORD_KINDS[key]:
            raise IntegrationAdmissionError(f"{key} admission evidence record_kind is unsupported")
        if record.get("synthetic_only") is not True:
            raise IntegrationAdmissionError(f"{key} admission evidence must remain synthetic_only")
        if record.get("production_action_authorized") is not False:
            raise IntegrationAdmissionError(f"{key} admission evidence cannot authorize production action")
        for field in self.REQUIRED_FIELDS[key]:
            if field not in record:
                raise IntegrationAdmissionError(f"{key} admission evidence is ambiguous: missing {field}")

        if key == "migration_prerequisites":
            if record.get("prerequisites_approved") is not True:
                return "ADMISSION_MIGRATION_PREREQUISITES_NOT_APPROVED"
            if (
                record.get("cutover_authorized") is not False
                or record.get("legacy_decommission_authorized") is not False
            ):
                raise IntegrationAdmissionError("migration evidence cannot authorize cutover/decommission")
        else:
            if key not in {"subscriber_delivery", "production_schedules"} and record.get("approved") is not True:
                return f"ADMISSION_{key.upper()}_NOT_APPROVED"

        if key == "discovery_adapter" and record.get("zero_incremental_cost") is not True:
            return "ADMISSION_DISCOVERY_ADAPTER_ZERO_COST_GUARD_FAILED"
        if key == "production_schedules":
            ids = record.get("schedule_identities")
            cadences = record.get("schedule_cadences")
            if not isinstance(ids, list) or not ids or not all(isinstance(x, str) and x for x in ids):
                raise IntegrationAdmissionError("production schedule identities are incomplete")
            if not isinstance(cadences, list) or len(cadences) != len(ids):
                raise IntegrationAdmissionError("production schedule cadences are incomplete")
            cadence_ids = [x.get("schedule_id") for x in cadences if isinstance(x, dict)]
            if cadence_ids != ids:
                raise IntegrationAdmissionError("production schedule identity/cadence binding is ambiguous")
        if key == "subscriber_delivery":
            if record.get("approved") is not True:
                return "ADMISSION_SUBSCRIBER_DELIVERY_POLICY_NOT_APPROVED"
        if key == "zero_incremental_cost":
            if record.get("zero_incremental_cost") is not True:
                return "ZERO_INCREMENTAL_COST_GUARD_FAILED"
            paid = (
                "separately_billed_openai_api_required",
                "paid_completion_or_storage_api_required",
                "paid_deployment_or_hosting_api_required",
                "other_incremental_paid_dependency_required",
            )
            if any(record.get(field) is not False for field in paid):
                return "ZERO_INCREMENTAL_COST_GUARD_FAILED"
        return None

    def _decision_binding(self, decision: dict[str, Any] | None) -> tuple[dict[str, Any], str | None]:
        if decision is None:
            return {
                "record_id": None,
                "decision_id": None,
                "record_digest": None,
                "decision": None,
            }, "ADMISSION_DECISION_MISSING"
        required = (
            "record_id",
            "record_kind",
            "decision_id",
            "decision",
            "approved",
            "synthetic_only",
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "scope",
            "plan_binding_mode",
        )
        missing = [key for key in required if key not in decision]
        if missing:
            raise IntegrationAdmissionError(
                f"admission decision is ambiguous: missing {','.join(missing)}"
            )
        if decision.get("record_kind") != "production-integration-admission-decision":
            raise IntegrationAdmissionError("admission decision record_kind is unsupported")
        if decision.get("synthetic_only") is not True:
            raise IntegrationAdmissionError("admission decision must remain synthetic_only")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if decision.get(flag) is not False:
                raise IntegrationAdmissionError(f"admission decision cannot authorize {flag}")
        if (
            decision.get("approved") is not True
            or decision.get("decision") != "authorization_ready_for_later_execution_review"
            or decision.get("scope") != "admission_only"
            or decision.get("plan_binding_mode") != "exact_locked_plan_artifact"
        ):
            return {
                "record_id": decision.get("record_id"),
                "decision_id": decision.get("decision_id"),
                "record_digest": digest(decision),
                "decision": decision.get("decision"),
            }, "ADMISSION_DECISION_NOT_APPROVED"
        return {
            "record_id": decision["record_id"],
            "decision_id": decision["decision_id"],
            "record_digest": digest(decision),
            "decision": decision["decision"],
        }, None

    def _evaluate(
        self, plan: dict[str, Any], policy: dict[str, Any], manifest: dict[str, Any]
    ) -> dict[str, Any]:
        bindings: dict[str, Any] = {}
        missing_or_blocking: list[str] = []
        for key in self.REQUIRED_EVIDENCE:
            record = manifest["evidence"][key]
            if record is None:
                bindings[key] = {
                    "evidence_source": "missing",
                    "record_id": None,
                    "record_digest": None,
                    "explicit_references": {},
                }
                missing_or_blocking.append(self.MISSING_REASON_CODES[key])
                continue
            reason = self._validate_present_evidence(key, record)
            bindings[key] = {
                "evidence_source": "repository_admission_manifest",
                "record_id": record["record_id"],
                "record_digest": digest(record),
                "explicit_references": self._explicit_references(record),
            }
            if reason:
                missing_or_blocking.append(reason)

        decision_binding, decision_reason = self._decision_binding(manifest.get("admission_decision"))
        if decision_reason:
            missing_or_blocking.append(decision_reason)

        if plan["plan_classification"] == "invalid":
            classification = "invalid"
            reason_codes = ["ITERATION12_PLAN_INVALID", *plan["plan_reason_codes"]]
        elif plan["plan_classification"] == "blocked":
            classification = "blocked"
            reason_codes = ["ITERATION12_PLAN_BLOCKED", *plan["plan_reason_codes"]]
        elif plan["plan_classification"] == "planned":
            if missing_or_blocking:
                classification = "blocked"
                reason_codes = missing_or_blocking
            else:
                classification = "authorization_ready"
                reason_codes = [policy["authorization_ready_reason_code"]]
        else:
            raise IntegrationAdmissionError("unsupported Iteration 12 plan classification")

        if classification == "authorization_ready":
            if plan["plan_classification"] != "planned":
                raise IntegrationAdmissionError("blocked/invalid plan cannot silently become authorization_ready")
            if decision_binding["decision_id"] is None:
                raise IntegrationAdmissionError("authorization_ready requires a separate admission decision")

        return {
            "classification": classification,
            "classification_reason_codes": reason_codes,
            "evidence_bindings": bindings,
            "admission_decision_binding": decision_binding,
        }

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        plan = self._plan_context(run)
        policy, manifest = self._policy_and_manifest()
        input_identity = {
            "plan_artifact_digest": plan["plan_artifact_digest"],
            "plan_id": plan["plan_id"],
            "admission_policy_digest": digest(policy),
            "admission_manifest_digest": digest(manifest),
        }
        state = self._load_state(input_identity)
        state["metrics"]["admission_validation_checks"] += 1
        if state.get("evaluation") is not None:
            state["metrics"]["admission_evaluation_reuse"] += 1
            state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._save_state(state)
            self._write_metrics(state)
            return deepcopy(state["evaluation"])

        state["attempts"]["admission_evaluation"] += 1
        state["metrics"]["admission_evaluation_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "evaluation" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("evaluation", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationAdmissionBoundaryFailure(
                "integration_admission_evaluation", "evaluation", self.failure_class
            )

        evaluated = self._evaluate(plan, policy, manifest)
        state["evaluation"] = {
            **evaluated,
            "input_identity": input_identity,
            "admission_policy_version": policy["integration_admission_policy_version"],
            "admission_policy_id": policy["policy_id"],
            "admission_manifest_id": manifest["manifest_id"],
            **deepcopy(plan),
        }
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state(state)
        self._write_metrics(state)
        return deepcopy(state["evaluation"])

    def _admission_data(self, run: dict[str, Any], evaluated: dict[str, Any]) -> dict[str, Any]:
        identity = evaluated["input_identity"]
        decision = evaluated["admission_decision_binding"]
        semantic_identity = {
            "admission_schema_version": ADMISSION_SCHEMA_VERSION,
            "admission_policy_version": evaluated["admission_policy_version"],
            "admission_policy_id": evaluated["admission_policy_id"],
            "admission_policy_digest": identity["admission_policy_digest"],
            "admission_manifest_id": evaluated["admission_manifest_id"],
            "admission_manifest_digest": identity["admission_manifest_digest"],
            "plan_artifact_digest": evaluated["plan_artifact_digest"],
            "plan_id": evaluated["plan_id"],
            "plan_schema_version": evaluated["plan_schema_version"],
            "plan_policy_version": evaluated["plan_policy_version"],
            "plan_policy_id": evaluated["plan_policy_id"],
            "plan_policy_digest": evaluated["plan_policy_digest"],
            "plan_classification": evaluated["plan_classification"],
            "plan_reason_codes": evaluated["plan_reason_codes"],
            "plan_graph_digest": evaluated["plan_graph_digest"],
            "dry_run_assertion_set_digest": evaluated["dry_run_assertion_set_digest"],
            "rollback_boundary_set_digest": evaluated["rollback_boundary_set_digest"],
            "preflight_artifact_digest": evaluated["preflight_artifact_digest"],
            "preflight_id": evaluated["preflight_id"],
            "readiness_artifact_digest": evaluated["readiness_artifact_digest"],
            "readiness_assessment_id": evaluated["readiness_assessment_id"],
            "completion_artifact_digest": evaluated["completion_artifact_digest"],
            "final_completion_receipt_digest": evaluated["final_completion_receipt_digest"],
            "canonical_chain_digest": evaluated["canonical_chain_digest"],
            "classification": evaluated["classification"],
            "classification_reason_codes": evaluated["classification_reason_codes"],
            "evidence_bindings": evaluated["evidence_bindings"],
            "admission_decision_id": decision["decision_id"],
            "admission_decision_digest": decision["record_digest"],
        }
        return {
            **semantic_identity,
            "admission_id": digest(semantic_identity),
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_admission_only",
            "synthetic_only": True,
            "production_action_authorized": False,
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "production_publication": False,
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
        if existing.get("status") != "locked":
            raise IntegrationAdmissionBoundaryFailure(
                "admission_validation", "admission_artifact", "cached admission artifact is not locked"
            )
        if semantic_digest(existing) != existing.get("content_digest"):
            raise IntegrationAdmissionBoundaryFailure(
                "admission_validation", "admission_artifact", "cached admission artifact is corrupted"
            )
        if existing.get("data") != self._admission_data(run, evaluated):
            raise IntegrationAdmissionBoundaryFailure(
                "admission_validation",
                "admission_artifact",
                "cached admission artifact binds different plan/policy/manifest identities",
            )
        state = self._load_state(evaluated["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_admission(self, run: dict[str, Any], evaluated: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "final_admission_artifact" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("final_admission_artifact", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationAdmissionBoundaryFailure(
                "integration_admission_artifact_assembly",
                "final_admission_artifact",
                self.failure_class,
            )
        return self._admission_data(run, evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationAdmissionError("final production integration admission artifact is not locked")
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationAdmissionError("final production integration admission artifact digest is invalid")
        data = artifact.get("data") or {}
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_private_command_center_mutated",
            "public_site_mutated",
            "production_schedule_action",
            "legacy_content_migrated",
            "incremental_paid_dependency_added",
        ):
            if data.get(flag) is not False:
                raise IntegrationAdmissionError(f"integration admission cannot authorize/mutate {flag}")
        if data.get("classification") == "authorization_ready":
            if data.get("plan_classification") != "planned":
                raise IntegrationAdmissionError("blocked/invalid plan cannot silently become authorization_ready")
            if not data.get("admission_decision_id"):
                raise IntegrationAdmissionError("authorization_ready requires an explicit admission decision")
        state = self._load_state()
        classification = data.get("classification")
        if classification == "blocked":
            state["metrics"]["blocked_classifications"] += 1
        elif classification == "authorization_ready":
            state["metrics"]["authorization_ready_classifications"] += 1
        elif classification == "invalid":
            state["metrics"]["invalid_classifications"] += 1
        else:
            raise IntegrationAdmissionError("unsupported integration admission classification")
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
