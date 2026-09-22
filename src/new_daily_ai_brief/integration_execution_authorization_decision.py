from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    EXECUTION_AUTHORIZATION_DECISION_POLICY_VERSION,
    EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION,
    EXECUTION_AUTHORIZATION_REVIEW_POLICY_VERSION,
    EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest


class IntegrationExecutionAuthorizationDecisionError(ContractError):
    pass


class IntegrationExecutionAuthorizationDecisionBoundaryFailure(
    IntegrationExecutionAuthorizationDecisionError
):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id


class ProductionIntegrationExecutionAuthorizationDecision:
    """Deterministic synthetic-only Iteration 17 authorization-decision boundary."""

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

    REVIEW_IDENTITY_FIELDS = (
        "authorization_review_schema_version",
        "authorization_review_policy_version",
        "authorization_review_policy_id",
        "authorization_review_policy_digest",
        "authorization_review_manifest_id",
        "authorization_review_manifest_digest",
        "authorization_review_decision_id",
        "authorization_review_decision_digest",
        "execution_rehearsal_artifact_digest",
        "execution_rehearsal_id",
        "rehearsal_classification",
        "rehearsal_reason_codes",
        "execution_attempt_id",
        "rehearsal_policy_id",
        "rehearsal_policy_digest",
        "rehearsal_manifest_id",
        "rehearsal_manifest_digest",
        "rehearsal_decision_id",
        "rehearsal_decision_digest",
        "rehearsal_receipt_ids",
        "rehearsal_receipt_set_digest",
        "receipt_verification_ids",
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
        "classification",
        "classification_reason_codes",
        "authorization_review_evidence_bindings",
    )

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_integration_execution_authorization_decision_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = fixture_root
        self.failure_boundary_id = (
            failure_boundary_id.removeprefix("authorization_decision:")
            if failure_boundary_id
            else None
        )
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "authorization-decision-state.json"
        self.metrics_path = self.store.run_dir / "authorization-decision-metrics.json"
        self.incident_path = self.store.run_dir / "authorization-decision-incident.json"

    def _read_json_fixture(self, name: str, *, optional: bool = False) -> dict[str, Any] | None:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionAuthorizationDecisionError(
                "production authorization-decision execution is intentionally unconfigured"
            )
        path = self.fixture_root / name
        if not path.exists():
            if optional:
                return None
            raise IntegrationExecutionAuthorizationDecisionError(
                f"authorization-decision fixture missing: {name}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _assert_authority_false(self, record: dict[str, Any], label: str) -> None:
        for flag in self.AUTHORITY_FLAGS:
            if record.get(flag) is not False:
                raise IntegrationExecutionAuthorizationDecisionError(
                    f"{label} must keep {flag}=false"
                )
        if record.get("real_integration_steps_enabled", 0) != 0:
            raise IntegrationExecutionAuthorizationDecisionError(
                f"{label} cannot enable real integration steps"
            )

    def _locked(self, artifact_type: str) -> dict[str, Any]:
        artifact = self.store.load_artifact(artifact_type)
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionAuthorizationDecisionError(
                f"locked artifact missing: {artifact_type}"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionAuthorizationDecisionError(
                f"locked artifact corrupted: {artifact_type}"
            )
        return artifact

    def _review_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        return {key: deepcopy(data.get(key)) for key in self.REVIEW_IDENTITY_FIELDS}

    def _context(self, run: dict[str, Any]) -> dict[str, Any]:
        if (
            run.get("current_state") != "Complete"
            or run.get("completion_status") != "complete_locked"
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "integration_execution_authorization_decision_only requires Complete / complete_locked"
            )

        review = self._locked("production-integration-execution-authorization-review")
        rd = review.get("data") or {}
        if (
            rd.get("authorization_review_schema_version")
            != EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION
            or rd.get("authorization_review_policy_version")
            != EXECUTION_AUTHORIZATION_REVIEW_POLICY_VERSION
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 16 authorization-review version unsupported"
            )
        if digest(self._review_identity(rd)) != rd.get("authorization_review_id"):
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 16 authorization-review identity is corrupted"
            )
        if (
            rd.get("final_state") != "Complete"
            or rd.get("final_status") != "complete_locked"
            or rd.get("completion_scope")
            != "synthetic_shadow_execution_authorization_review_only"
            or rd.get("synthetic_only") is not True
            or rd.get("real_integration_steps_enabled") != 0
            or rd.get("real_integration_steps_executed") != 0
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 16 authorization-review semantics are stale"
            )
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
            "real_executor_invocation_authorized",
            "credentials_use_authorized",
        ):
            if rd.get(flag) is not False:
                raise IntegrationExecutionAuthorizationDecisionError(
                    f"Iteration 16 authorization review cannot authorize {flag}"
                )
        if any(x.get("enabled") is not False for x in rd.get("execution_steps") or []):
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 16 real integration steps must remain disabled"
            )

        rehearsal = self._locked("production-integration-execution-rehearsal")
        execution_preflight = self._locked("production-integration-execution-preflight")
        admission = self._locked("production-integration-admission")
        plan = self._locked("production-integration-plan")
        preflight = self._locked("production-integration-preflight")
        readiness = self._locked("readiness-admission")
        completion = self._locked("completion")

        checks = (
            (rd.get("execution_rehearsal_artifact_digest"), rehearsal["content_digest"], "rehearsal digest"),
            (rd.get("execution_rehearsal_id"), rehearsal["data"].get("execution_rehearsal_id"), "rehearsal id"),
            (rd.get("execution_attempt_id"), rehearsal["data"].get("execution_attempt_id"), "execution attempt"),
            (rd.get("execution_preflight_artifact_digest"), execution_preflight["content_digest"], "execution preflight digest"),
            (rd.get("execution_preflight_id"), execution_preflight["data"].get("execution_preflight_id"), "execution preflight id"),
            (rd.get("admission_artifact_digest"), admission["content_digest"], "admission digest"),
            (rd.get("admission_id"), admission["data"].get("admission_id"), "admission id"),
            (rd.get("plan_artifact_digest"), plan["content_digest"], "plan digest"),
            (rd.get("plan_id"), plan["data"].get("plan_id"), "plan id"),
            (rd.get("preflight_artifact_digest"), preflight["content_digest"], "preflight digest"),
            (rd.get("preflight_id"), preflight["data"].get("preflight_id"), "preflight id"),
            (rd.get("readiness_artifact_digest"), readiness["content_digest"], "readiness digest"),
            (rd.get("readiness_assessment_id"), readiness["data"].get("assessment_id"), "readiness id"),
            (rd.get("completion_artifact_digest"), completion["content_digest"], "completion digest"),
        )
        for actual, expected, label in checks:
            if actual != expected:
                raise IntegrationExecutionAuthorizationDecisionError(
                    f"Iteration 16 {label} binding changed"
                )

        rehearsal_data = rehearsal["data"]
        if rd.get("rehearsal_policy_id") != rehearsal_data.get("execution_rehearsal_policy_id"):
            raise IntegrationExecutionAuthorizationDecisionError("Iteration 15 rehearsal policy id changed")
        if rd.get("rehearsal_policy_digest") != rehearsal_data.get("execution_rehearsal_policy_digest"):
            raise IntegrationExecutionAuthorizationDecisionError("Iteration 15 rehearsal policy digest changed")
        if rd.get("rehearsal_manifest_id") != rehearsal_data.get("rehearsal_envelope_manifest_id"):
            raise IntegrationExecutionAuthorizationDecisionError("Iteration 15 rehearsal manifest id changed")
        if rd.get("rehearsal_manifest_digest") != rehearsal_data.get("rehearsal_envelope_manifest_digest"):
            raise IntegrationExecutionAuthorizationDecisionError("Iteration 15 rehearsal manifest digest changed")
        if rd.get("rehearsal_decision_id") != rehearsal_data.get("rehearsal_decision_id"):
            raise IntegrationExecutionAuthorizationDecisionError("Iteration 15 rehearsal decision id changed")
        if rd.get("rehearsal_decision_digest") != rehearsal_data.get("rehearsal_decision_digest"):
            raise IntegrationExecutionAuthorizationDecisionError("Iteration 15 rehearsal decision digest changed")

        receipts = rehearsal_data.get("rehearsal_receipts") or []
        expected_receipt_ids = [x.get("receipt_id") for x in receipts]
        if rd.get("rehearsal_receipt_ids") != expected_receipt_ids:
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 15 ordered rehearsal receipt ids changed"
            )
        if rd.get("rehearsal_receipt_set_digest") != digest(receipts):
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 15 rehearsal receipt-set digest changed"
            )

        plan_data = plan["data"]
        if rd.get("plan_graph_digest") != digest(plan_data.get("plan_steps") or []):
            raise IntegrationExecutionAuthorizationDecisionError("Iteration 12 plan graph changed")
        if rd.get("dry_run_assertion_set_digest") != digest(plan_data.get("dry_run_assertion_set") or []):
            raise IntegrationExecutionAuthorizationDecisionError("dry-run assertion set changed")
        if rd.get("rollback_boundary_set_digest") != digest(plan_data.get("rollback_boundary_set") or []):
            raise IntegrationExecutionAuthorizationDecisionError("rollback boundary set changed")

        verifications = deepcopy(rd.get("receipt_verifications") or [])
        verification_ids = [x.get("verification_id") for x in verifications]
        if rd.get("receipt_verification_ids") != verification_ids:
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 16 receipt-verification id inventory changed"
            )
        if len(verification_ids) != len(set(verification_ids)):
            raise IntegrationExecutionAuthorizationDecisionError(
                "Iteration 16 receipt-verification ids duplicated"
            )
        classification = rd.get("classification")
        if classification == "authorization_review_ready":
            if len(verifications) != 10 or rd.get("receipt_verification_count") != 10:
                raise IntegrationExecutionAuthorizationDecisionError(
                    "authorization_review_ready requires exactly ten verifications"
                )
            if [x.get("position") for x in verifications] != list(range(1, 11)):
                raise IntegrationExecutionAuthorizationDecisionError(
                    "Iteration 16 receipt-verification order changed"
                )
            if not all(
                x.get("noop_verified") is True
                and x.get("side_effect_free_verified") is True
                for x in verifications
            ):
                raise IntegrationExecutionAuthorizationDecisionError(
                    "Iteration 16 receipt verification is not no-op/side-effect-free"
                )
            if (
                not rd.get("authorization_review_decision_id")
                or not rd.get("authorization_review_decision_digest")
            ):
                raise IntegrationExecutionAuthorizationDecisionError(
                    "authorization_review_ready lacks separate review-decision identity"
                )
        elif classification == "blocked":
            if verifications or rd.get("receipt_verification_count") != 0:
                raise IntegrationExecutionAuthorizationDecisionError(
                    "blocked Iteration 16 review cannot carry receipt verifications"
                )
        elif classification != "invalid":
            raise IntegrationExecutionAuthorizationDecisionError(
                "unsupported Iteration 16 authorization-review classification"
            )

        return {
            "authorization_review_artifact_digest": review["content_digest"],
            "authorization_review_id": rd["authorization_review_id"],
            "authorization_review_classification": classification,
            "authorization_review_reason_codes": deepcopy(
                rd.get("classification_reason_codes") or []
            ),
            "authorization_review_policy_id": rd.get("authorization_review_policy_id"),
            "authorization_review_policy_digest": rd.get("authorization_review_policy_digest"),
            "authorization_review_manifest_id": rd.get("authorization_review_manifest_id"),
            "authorization_review_manifest_digest": rd.get("authorization_review_manifest_digest"),
            "authorization_review_decision_id": rd.get("authorization_review_decision_id"),
            "authorization_review_decision_digest": rd.get("authorization_review_decision_digest"),
            "review_receipt_verifications": verifications,
            "review_receipt_verification_ids": verification_ids,
            "review_receipt_verification_digests": [digest(x) for x in verifications],
            "review_receipt_verification_set_digest": digest(verifications),
            "execution_rehearsal_artifact_digest": rd.get("execution_rehearsal_artifact_digest"),
            "execution_rehearsal_id": rd.get("execution_rehearsal_id"),
            "execution_attempt_id": rd.get("execution_attempt_id"),
            "rehearsal_policy_id": rd.get("rehearsal_policy_id"),
            "rehearsal_policy_digest": rd.get("rehearsal_policy_digest"),
            "rehearsal_manifest_id": rd.get("rehearsal_manifest_id"),
            "rehearsal_manifest_digest": rd.get("rehearsal_manifest_digest"),
            "rehearsal_decision_id": rd.get("rehearsal_decision_id"),
            "rehearsal_decision_digest": rd.get("rehearsal_decision_digest"),
            "rehearsal_receipt_ids": deepcopy(rd.get("rehearsal_receipt_ids") or []),
            "rehearsal_receipt_set_digest": rd.get("rehearsal_receipt_set_digest"),
            "execution_preflight_artifact_digest": rd.get("execution_preflight_artifact_digest"),
            "execution_preflight_id": rd.get("execution_preflight_id"),
            "admission_artifact_digest": rd.get("admission_artifact_digest"),
            "admission_id": rd.get("admission_id"),
            "plan_artifact_digest": rd.get("plan_artifact_digest"),
            "plan_id": rd.get("plan_id"),
            "plan_graph_digest": rd.get("plan_graph_digest"),
            "dry_run_assertion_set_digest": rd.get("dry_run_assertion_set_digest"),
            "rollback_boundary_set_digest": rd.get("rollback_boundary_set_digest"),
            "preflight_artifact_digest": rd.get("preflight_artifact_digest"),
            "preflight_id": rd.get("preflight_id"),
            "readiness_artifact_digest": rd.get("readiness_artifact_digest"),
            "readiness_assessment_id": rd.get("readiness_assessment_id"),
            "completion_artifact_digest": rd.get("completion_artifact_digest"),
            "final_completion_receipt_digest": rd.get("final_completion_receipt_digest"),
            "canonical_chain_digest": rd.get("canonical_chain_digest"),
            "execution_steps": deepcopy(rd.get("execution_steps") or []),
        }

    def _policy_manifest_decision(
        self, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        policy = self._read_json_fixture("authorization-decision-policy.json")
        manifest = self._read_json_fixture("authorization-decision-manifest.json")
        decision = self._read_json_fixture("authorization-decision-record.json", optional=True)
        assert policy is not None and manifest is not None
        if (
            policy.get("schema_version") != EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION
            or policy.get("authorization_decision_policy_version")
            != EXECUTION_AUTHORIZATION_DECISION_POLICY_VERSION
            or policy.get("policy_id")
            != "production-integration-execution-authorization-decision-v1"
            or policy.get("synthetic_only") is not True
            or policy.get("real_authority_permitted") is not False
            or policy.get("zero_incremental_cost_required") is not True
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision policy unsupported"
            )
        if (
            manifest.get("schema_version") != EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION
            or manifest.get("authorization_decision_manifest_version") != "1.0.0"
            or manifest.get("manifest_id")
            != "production-integration-execution-authorization-decision-manifest-v1"
            or manifest.get("synthetic_only") is not True
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision manifest unsupported"
            )
        self._assert_authority_false(manifest, "authorization-decision manifest")
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
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision evidence envelope incomplete"
            )
        if evidence["executor_declaration"] != {
            "real_executor_required": False,
            "real_executor_present": False,
            "real_executor_invocation_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationDecisionError("executor declaration unsafe")
        if evidence["credential_declaration"] != {
            "credentials_required": False,
            "credentials_present": False,
            "credentials_use_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationDecisionError("credential declaration unsafe")
        if evidence["target_declaration"] != {
            "scope": "synthetic_non_production",
            "real_target_present": False,
            "real_target_contact_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationDecisionError("target declaration unsafe")
        if evidence["rollback_declaration"] != {
            "rollback_plan_bound": True,
            "rollback_execution_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationDecisionError("rollback declaration unsafe")
        if evidence["cost_declaration"] != {
            "incremental_paid_dependency_required": False,
            "zero_incremental_cost_approved": True,
        }:
            raise IntegrationExecutionAuthorizationDecisionError(
                "zero-incremental-cost declaration missing"
            )
        expected_abort = {
            "identity_mismatch",
            "authority_flag_true",
            "cost_guard_failed",
            "receipt_or_provenance_mismatch",
        }
        if set(evidence["stop_abort_conditions"]) != expected_abort:
            raise IntegrationExecutionAuthorizationDecisionError(
                "stop/abort conditions incomplete"
            )
        self._assert_authority_false(evidence["authority_state"], "authority state")
        return policy, manifest, decision

    def _decision_id(self, decision: dict[str, Any]) -> str:
        body = deepcopy(decision)
        body.pop("decision_id", None)
        return digest(body)

    def _decision_binding(
        self,
        decision: dict[str, Any] | None,
        context: dict[str, Any],
        manifest: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None]:
        if decision is None:
            return {"decision_id": None, "decision_digest": None}, "AUTHORIZATION_DECISION_RECORD_MISSING"
        if (
            decision.get("schema_version") != EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION
            or decision.get("decision_version") != "1.0.0"
            or decision.get("record_kind")
            != "production-integration-execution-authorization-decision-record"
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision record version unsupported"
            )
        if decision.get("decision_id") != self._decision_id(decision):
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision identity changed"
            )
        self._assert_authority_false(decision, "authorization-decision record")
        if (
            decision.get("synthetic_only") is not True
            or decision.get("approved") is not True
            or decision.get("decision")
            != "admit_synthetic_authorization_decision_boundary"
            or decision.get("scope") != "authorization_decision_only"
            or decision.get("grants_production_authority") is not False
            or decision.get("zero_incremental_cost_approved") is not True
            or decision.get("authorization_review_id") != context["authorization_review_id"]
            or decision.get("authorization_review_artifact_digest")
            != context["authorization_review_artifact_digest"]
            or decision.get("authorization_review_policy_id")
            != context["authorization_review_policy_id"]
            or decision.get("authorization_review_policy_digest")
            != context["authorization_review_policy_digest"]
            or decision.get("authorization_review_manifest_id")
            != context["authorization_review_manifest_id"]
            or decision.get("authorization_review_manifest_digest")
            != context["authorization_review_manifest_digest"]
            or decision.get("authorization_review_decision_id")
            != context["authorization_review_decision_id"]
            or decision.get("authorization_review_decision_digest")
            != context["authorization_review_decision_digest"]
            or decision.get("review_receipt_verification_set_digest")
            != context["review_receipt_verification_set_digest"]
            or decision.get("authorization_decision_manifest_id")
            != manifest["manifest_id"]
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision record binding changed"
            )
        return {
            "decision_id": decision["decision_id"],
            "decision_digest": digest(decision),
        }, None

    def _evaluate(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        decision: dict[str, Any] | None,
    ) -> dict[str, Any]:
        classification = context["authorization_review_classification"]
        if classification == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION16_AUTHORIZATION_REVIEW_INVALID",
                    *context["authorization_review_reason_codes"],
                ],
                "authorization_decision_binding": {
                    "decision_id": None,
                    "decision_digest": None,
                },
            }
        if classification == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION16_AUTHORIZATION_REVIEW_BLOCKED",
                    *context["authorization_review_reason_codes"],
                ],
                "authorization_decision_binding": {
                    "decision_id": None,
                    "decision_digest": None,
                },
            }

        binding = manifest.get("authorization_review_binding") or {}
        expected = {
            "binding_mode": "exact_locked_authorization_review_artifact",
            "authorization_review_artifact_digest": context["authorization_review_artifact_digest"],
            "authorization_review_id": context["authorization_review_id"],
            "authorization_review_policy_id": context["authorization_review_policy_id"],
            "authorization_review_policy_digest": context["authorization_review_policy_digest"],
            "authorization_review_manifest_id": context["authorization_review_manifest_id"],
            "authorization_review_manifest_digest": context["authorization_review_manifest_digest"],
            "authorization_review_decision_id": context["authorization_review_decision_id"],
            "authorization_review_decision_digest": context["authorization_review_decision_digest"],
            "review_receipt_verification_ids": context["review_receipt_verification_ids"],
            "review_receipt_verification_digests": context["review_receipt_verification_digests"],
            "review_receipt_verification_set_digest": context["review_receipt_verification_set_digest"],
        }
        if binding != expected:
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision manifest binds a different Iteration 16 identity"
            )

        decision_binding, reason = self._decision_binding(decision, context, manifest)
        if reason:
            return {
                "classification": "blocked",
                "classification_reason_codes": [reason],
                "authorization_decision_binding": decision_binding,
            }
        return {
            "classification": "authorization_decision_ready",
            "classification_reason_codes": ["SYNTHETIC_AUTHORIZATION_DECISION_READY"],
            "authorization_decision_binding": decision_binding,
        }

    def _input_identity(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        decision: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "authorization_review_artifact_digest": context["authorization_review_artifact_digest"],
            "authorization_review_id": context["authorization_review_id"],
            "authorization_decision_policy_digest": digest(policy),
            "authorization_decision_manifest_digest": digest(manifest),
            "authorization_decision_record_digest": digest(decision) if decision else None,
            "authorization_decision_record_id": decision.get("decision_id") if decision else None,
        }

    def _new_state(self, identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION,
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
                "blocked_classifications": 0,
                "authorization_decision_ready_classifications": 0,
                "invalid_classifications": 0,
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
                raise IntegrationExecutionAuthorizationDecisionError(
                    "authorization-decision state missing"
                )
            return self._new_state(identity)
        if (
            state.get("schema_version") != EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision durable state version changed"
            )
        if identity is not None and state.get("input_identity") != identity:
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision durable state binds different inputs"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION,
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
                "schema_version": EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION,
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
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision incident binds different inputs"
            )
        incident["result"] = "recovered"
        self.store._atomic_write(self.incident_path, incident)

    def _validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"authorization-decision-verification-{position:02d}.json"

    def _validation_record(
        self, context: dict[str, Any], position: int, verification: dict[str, Any]
    ) -> dict[str, Any]:
        body = {
            "schema_version": EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION,
            "authorization_review_id": context["authorization_review_id"],
            "position": position,
            "source_verification_id": verification["verification_id"],
            "source_verification_digest": digest(verification),
            "noop_verified": verification.get("noop_verified"),
            "side_effect_free_verified": verification.get("side_effect_free_verified"),
        }
        return {**body, "validation_id": digest(body)}

    def _ensure_provenance_validations(
        self, context: dict[str, Any], evaluated: dict[str, Any], state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if evaluated["classification"] != "authorization_decision_ready":
            return []
        result: list[dict[str, Any]] = []
        for position, verification in enumerate(
            context["review_receipt_verifications"], start=1
        ):
            if (
                verification.get("noop_verified") is not True
                or verification.get("side_effect_free_verified") is not True
            ):
                raise IntegrationExecutionAuthorizationDecisionError(
                    "source receipt verification is unsafe"
                )
            expected = self._validation_record(context, position, verification)
            path = self._validation_path(position)
            existing = self.store.read_json(path)
            key = str(position)
            state["attempts"]["validations"].setdefault(key, 0)
            if existing is not None:
                if existing != expected:
                    raise IntegrationExecutionAuthorizationDecisionError(
                        f"cached provenance validation changed at position {position}"
                    )
                state["metrics"]["provenance_validation_reuse"] += 1
                state["validation_digests"][key] = digest(existing)
                result.append(existing)
                continue
            state["attempts"]["validations"][key] += 1
            state["metrics"]["provenance_validation_attempts"] += 1
            self._save_state(state)
            boundary = f"verification:{position}"
            if self.failure_boundary_id == boundary and not self._failure_fired:
                self._failure_fired = True
                self._record_incident(boundary, state)
                self._write_metrics(state)
                raise IntegrationExecutionAuthorizationDecisionBoundaryFailure(
                    "authorization_decision_provenance_validation",
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
        policy, manifest, decision = self._policy_manifest_decision(context)
        identity = self._input_identity(context, policy, manifest, decision)
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
                raise IntegrationExecutionAuthorizationDecisionBoundaryFailure(
                    "authorization_decision_evaluation",
                    "evaluation",
                    self.failure_class,
                )
            outcome = self._evaluate(context, policy, manifest, decision)
            state["evaluation"] = {
                **deepcopy(context),
                **outcome,
                "input_identity": deepcopy(identity),
                "authorization_decision_policy_id": policy["policy_id"],
                "authorization_decision_policy_version": policy[
                    "authorization_decision_policy_version"
                ],
                "authorization_decision_manifest_id": manifest["manifest_id"],
            }
            self._save_state(state)
        else:
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        validations = self._ensure_provenance_validations(context, evaluated, state)
        evaluated["provenance_validations"] = validations
        state["evaluation"]["provenance_validation_ids"] = [
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
        decision = evaluated["authorization_decision_binding"]
        identity = {
            "authorization_decision_schema_version": EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION,
            "authorization_decision_policy_version": evaluated[
                "authorization_decision_policy_version"
            ],
            "authorization_decision_policy_id": evaluated["authorization_decision_policy_id"],
            "authorization_decision_policy_digest": evaluated["input_identity"][
                "authorization_decision_policy_digest"
            ],
            "authorization_decision_manifest_id": evaluated[
                "authorization_decision_manifest_id"
            ],
            "authorization_decision_manifest_digest": evaluated["input_identity"][
                "authorization_decision_manifest_digest"
            ],
            "separate_authorization_decision_id": decision.get("decision_id"),
            "separate_authorization_decision_digest": decision.get("decision_digest"),
            "authorization_review_artifact_digest": evaluated[
                "authorization_review_artifact_digest"
            ],
            "authorization_review_id": evaluated["authorization_review_id"],
            "authorization_review_classification": evaluated[
                "authorization_review_classification"
            ],
            "authorization_review_reason_codes": evaluated[
                "authorization_review_reason_codes"
            ],
            "authorization_review_policy_id": evaluated["authorization_review_policy_id"],
            "authorization_review_policy_digest": evaluated[
                "authorization_review_policy_digest"
            ],
            "authorization_review_manifest_id": evaluated[
                "authorization_review_manifest_id"
            ],
            "authorization_review_manifest_digest": evaluated[
                "authorization_review_manifest_digest"
            ],
            "authorization_review_decision_id": evaluated[
                "authorization_review_decision_id"
            ],
            "authorization_review_decision_digest": evaluated[
                "authorization_review_decision_digest"
            ],
            "review_receipt_verification_ids": evaluated[
                "review_receipt_verification_ids"
            ],
            "review_receipt_verification_digests": evaluated[
                "review_receipt_verification_digests"
            ],
            "review_receipt_verification_set_digest": evaluated[
                "review_receipt_verification_set_digest"
            ],
            "provenance_validation_ids": [
                x["validation_id"] for x in evaluated["provenance_validations"]
            ],
            "provenance_validation_digests": [
                digest(x) for x in evaluated["provenance_validations"]
            ],
            "execution_rehearsal_artifact_digest": evaluated[
                "execution_rehearsal_artifact_digest"
            ],
            "execution_rehearsal_id": evaluated["execution_rehearsal_id"],
            "execution_attempt_id": evaluated["execution_attempt_id"],
            "rehearsal_policy_id": evaluated["rehearsal_policy_id"],
            "rehearsal_policy_digest": evaluated["rehearsal_policy_digest"],
            "rehearsal_manifest_id": evaluated["rehearsal_manifest_id"],
            "rehearsal_manifest_digest": evaluated["rehearsal_manifest_digest"],
            "rehearsal_decision_id": evaluated["rehearsal_decision_id"],
            "rehearsal_decision_digest": evaluated["rehearsal_decision_digest"],
            "rehearsal_receipt_ids": evaluated["rehearsal_receipt_ids"],
            "rehearsal_receipt_set_digest": evaluated["rehearsal_receipt_set_digest"],
            "execution_preflight_artifact_digest": evaluated[
                "execution_preflight_artifact_digest"
            ],
            "execution_preflight_id": evaluated["execution_preflight_id"],
            "admission_artifact_digest": evaluated["admission_artifact_digest"],
            "admission_id": evaluated["admission_id"],
            "plan_artifact_digest": evaluated["plan_artifact_digest"],
            "plan_id": evaluated["plan_id"],
            "plan_graph_digest": evaluated["plan_graph_digest"],
            "dry_run_assertion_set_digest": evaluated["dry_run_assertion_set_digest"],
            "rollback_boundary_set_digest": evaluated["rollback_boundary_set_digest"],
            "preflight_artifact_digest": evaluated["preflight_artifact_digest"],
            "preflight_id": evaluated["preflight_id"],
            "readiness_artifact_digest": evaluated["readiness_artifact_digest"],
            "readiness_assessment_id": evaluated["readiness_assessment_id"],
            "completion_artifact_digest": evaluated["completion_artifact_digest"],
            "final_completion_receipt_digest": evaluated[
                "final_completion_receipt_digest"
            ],
            "canonical_chain_digest": evaluated["canonical_chain_digest"],
            "classification": evaluated["classification"],
            "classification_reason_codes": evaluated["classification_reason_codes"],
        }
        return {
            **identity,
            "authorization_decision_id": digest(identity),
            "execution_steps": deepcopy(evaluated["execution_steps"]),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_execution_authorization_decision_only",
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
            raise IntegrationExecutionAuthorizationDecisionBoundaryFailure(
                "authorization_decision_validation",
                "authorization_decision_artifact",
                "cached authorization-decision artifact invalid",
            )
        if existing.get("data") != self._artifact_data(evaluated):
            raise IntegrationExecutionAuthorizationDecisionBoundaryFailure(
                "authorization_decision_validation",
                "authorization_decision_artifact",
                "cached authorization-decision artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        assert state is not None
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_authorization_decision(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        assert state is not None
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id == "final_authorization_decision_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._record_incident("final_authorization_decision_artifact", state)
            self._write_metrics(state)
            raise IntegrationExecutionAuthorizationDecisionBoundaryFailure(
                "authorization_decision_artifact_assembly",
                "final_authorization_decision_artifact",
                self.failure_class,
            )
        return self._artifact_data(evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionAuthorizationDecisionError(
                "final authorization-decision artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionAuthorizationDecisionError(
                "final authorization-decision artifact digest invalid"
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
                raise IntegrationExecutionAuthorizationDecisionError(
                    f"authorization-decision gate cannot authorize/mutate {flag}"
                )
        if (
            data.get("real_integration_steps_enabled") != 0
            or data.get("real_integration_steps_executed") != 0
            or any(x.get("enabled") is not False for x in data.get("execution_steps") or [])
        ):
            raise IntegrationExecutionAuthorizationDecisionError(
                "authorization-decision gate cannot enable/execute a real step"
            )
        classification = data.get("classification")
        if classification == "authorization_decision_ready":
            if data.get("authorization_review_classification") != "authorization_review_ready":
                raise IntegrationExecutionAuthorizationDecisionError(
                    "authorization_decision_ready requires authorization_review_ready"
                )
            if not data.get("separate_authorization_decision_id"):
                raise IntegrationExecutionAuthorizationDecisionError(
                    "authorization_decision_ready requires separate decision record"
                )
            if len(data.get("review_receipt_verification_ids") or []) != 10:
                raise IntegrationExecutionAuthorizationDecisionError(
                    "authorization_decision_ready requires ten review verifications"
                )
            if len(data.get("provenance_validation_ids") or []) != 10:
                raise IntegrationExecutionAuthorizationDecisionError(
                    "authorization_decision_ready requires ten provenance validations"
                )
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionAuthorizationDecisionError(
                "unsupported authorization-decision classification"
            )
        state = self._load_state()
        assert state is not None
        if classification == "blocked":
            state["metrics"]["blocked_classifications"] += 1
        elif classification == "authorization_decision_ready":
            state["metrics"]["authorization_decision_ready_classifications"] += 1
        else:
            state["metrics"]["invalid_classifications"] += 1
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
