from __future__ import annotations

import json
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    EXECUTION_AUTHORIZATION_REVIEW_POLICY_VERSION,
    EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION,
    EXECUTION_PREFLIGHT_POLICY_VERSION,
    EXECUTION_PREFLIGHT_SCHEMA_VERSION,
    EXECUTION_REHEARSAL_POLICY_VERSION,
    EXECUTION_REHEARSAL_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class IntegrationExecutionAuthorizationReviewError(ContractError):
    pass


class IntegrationExecutionAuthorizationReviewBoundaryFailure(
    IntegrationExecutionAuthorizationReviewError
):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"authorization_review:{boundary_id}"


class ProductionIntegrationExecutionAuthorizationReview:
    """Deterministic, synthetic-only Iteration 16 execution authorization-review gate."""

    REQUIRED_EVIDENCE = (
        "rehearsal_identity",
        "receipt_inventory",
        "receipt_verification",
        "executor_review_contract",
        "step_selection_scope",
        "target_environment",
        "credential_use_policy",
        "rollback_recovery_policy",
        "pre_execution_verification_review",
        "stop_abort_conditions",
        "cutover_decommission_state",
        "zero_incremental_cost",
    )
    MISSING_REASON_CODES = {
        "rehearsal_identity": "AUTH_REVIEW_REHEARSAL_IDENTITY_MISSING",
        "receipt_inventory": "AUTH_REVIEW_RECEIPT_INVENTORY_MISSING",
        "receipt_verification": "AUTH_REVIEW_RECEIPT_VERIFICATION_MISSING",
        "executor_review_contract": "AUTH_REVIEW_EXECUTOR_CONTRACT_MISSING",
        "step_selection_scope": "AUTH_REVIEW_STEP_SELECTION_SCOPE_MISSING",
        "target_environment": "AUTH_REVIEW_TARGET_ENVIRONMENT_MISSING",
        "credential_use_policy": "AUTH_REVIEW_CREDENTIAL_POLICY_MISSING",
        "rollback_recovery_policy": "AUTH_REVIEW_ROLLBACK_POLICY_MISSING",
        "pre_execution_verification_review": "AUTH_REVIEW_PRE_EXECUTION_VERIFICATION_MISSING",
        "stop_abort_conditions": "AUTH_REVIEW_STOP_ABORT_CONDITIONS_MISSING",
        "cutover_decommission_state": "AUTH_REVIEW_CUTOVER_DECOMMISSION_STATE_MISSING",
        "zero_incremental_cost": "AUTH_REVIEW_ZERO_INCREMENTAL_COST_GUARD_MISSING",
    }
    EXPECTED_RECORD_KINDS = {
        "rehearsal_identity": "production-integration-authorization-review-rehearsal-binding",
        "receipt_inventory": "production-integration-authorization-review-receipt-inventory",
        "receipt_verification": "production-integration-authorization-review-receipt-verification-policy",
        "executor_review_contract": "production-integration-authorization-review-executor-contract",
        "step_selection_scope": "production-integration-authorization-review-step-selection-scope",
        "target_environment": "production-integration-authorization-review-target-environment",
        "credential_use_policy": "production-integration-authorization-review-credential-policy",
        "rollback_recovery_policy": "production-integration-authorization-review-rollback-policy",
        "pre_execution_verification_review": "production-integration-authorization-review-pre-execution-verification-policy",
        "stop_abort_conditions": "production-integration-authorization-review-stop-abort-policy",
        "cutover_decommission_state": "production-integration-authorization-review-cutover-decommission-state",
        "zero_incremental_cost": "cost-policy-approval",
    }
    AUTHORITY_FLAGS = (
        "production_action_authorized",
        "production_cutover_authorized",
        "legacy_decommission_authorized",
        "production_publication",
        "real_executor_invocation_authorized",
        "credentials_use_authorized",
    )

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_integration_execution_authorization_review_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix(
            "authorization_review:"
        )
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = (
            self.store.run_dir / "iteration16-execution-authorization-review-state.json"
        )
        self.metrics_path = (
            self.store.run_dir / "iteration16-execution-authorization-review-metrics.json"
        )
        self.incident_path = (
            self.store.run_dir / "iteration16-execution-authorization-review-incident.json"
        )
        self.final_receipt_path = (
            self.store.run_dir / "iteration9-final-completion-receipt.json"
        )

    def _read_json_fixture(self, name: str) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionAuthorizationReviewError(
                "execution authorization review is synthetic-only and fail-closed"
            )
        path = self.fixture_root / name
        if not path.exists():
            raise IntegrationExecutionAuthorizationReviewError(
                f"missing Iteration 16 authorization-review fixture: {path}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _assert_authority_false(self, record: dict[str, Any], label: str) -> None:
        for flag in self.AUTHORITY_FLAGS:
            if record.get(flag) is not False:
                raise IntegrationExecutionAuthorizationReviewError(
                    f"{label} cannot authorize {flag}"
                )

    def _policy_and_manifest(self) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self._read_json_fixture("authorization-review-policy.json")
        manifest = self._read_json_fixture("authorization-review-manifest.json")
        if (
            policy.get("schema_version") != EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION
            or policy.get("authorization_review_policy_version")
            != EXECUTION_AUTHORIZATION_REVIEW_POLICY_VERSION
            or policy.get("policy_id")
            != "production-integration-execution-authorization-review-v1"
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "unsupported Iteration 16 authorization-review policy/schema identity"
            )
        if policy.get("synthetic_only") is not True:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review policy must remain synthetic_only"
            )
        self._assert_authority_false(policy, "authorization-review policy")
        if policy.get("require_exact_execution_rehearsal_binding") is not True:
            raise IntegrationExecutionAuthorizationReviewError(
                "exact Iteration 15 rehearsal binding is required"
            )
        if policy.get("require_separate_authorization_review_decision") is not True:
            raise IntegrationExecutionAuthorizationReviewError(
                "separate authorization-review decision is required"
            )
        if policy.get("require_exactly_ten_verified_noop_receipts") is not True:
            raise IntegrationExecutionAuthorizationReviewError(
                "exactly ten verified no-op receipts are required"
            )
        if tuple(policy.get("required_evidence") or ()) != self.REQUIRED_EVIDENCE:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review evidence inventory is incomplete"
            )
        if policy.get("classifications") != [
            "blocked",
            "authorization_review_ready",
            "invalid",
        ]:
            raise IntegrationExecutionAuthorizationReviewError(
                "unsupported authorization-review classifications"
            )
        if (
            manifest.get("schema_version") != EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION
            or manifest.get("authorization_review_manifest_version") != "1.0.0"
            or not manifest.get("manifest_id")
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "unsupported authorization-review manifest identity"
            )
        if manifest.get("synthetic_only") is not True:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review manifest must remain synthetic_only"
            )
        self._assert_authority_false(manifest, "authorization-review manifest")
        closure = manifest.get("iteration15_closure") or {}
        if (
            closure.get("repository_closure_status") != "complete"
            or closure.get("iteration16_ready") is not True
            or closure.get("evidence_path")
            != "evidence/iteration15/synthetic-shadow-production-integration-execution-rehearsal-evidence.json"
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 15 closure is incomplete or untrusted"
            )
        if (manifest.get("execution_rehearsal_binding") or {}) != {
            "binding_type": "exact_locked_execution_rehearsal_artifact",
            "artifact_type": "production-integration-execution-rehearsal",
            "execution_rehearsal_id_field": "data.execution_rehearsal_id",
            "artifact_digest_field": "content_digest",
        }:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review rehearsal binding declaration is invalid"
            )
        evidence = manifest.get("evidence")
        if not isinstance(evidence, dict) or tuple(evidence.keys()) != self.REQUIRED_EVIDENCE:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review evidence map is incomplete or ambiguous"
            )
        decision = manifest.get("authorization_review_decision")
        if decision is not None and not isinstance(decision, dict):
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review decision must be explicit record or null"
            )
        return policy, manifest

    def _rehearsal_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        keys = (
            "execution_rehearsal_schema_version",
            "execution_rehearsal_policy_version",
            "execution_rehearsal_policy_id",
            "execution_rehearsal_policy_digest",
            "rehearsal_envelope_manifest_id",
            "rehearsal_envelope_manifest_digest",
            "rehearsal_decision_id",
            "rehearsal_decision_digest",
            "execution_preflight_artifact_digest",
            "execution_preflight_id",
            "execution_preflight_classification",
            "execution_preflight_reason_codes",
            "execution_preflight_policy_id",
            "execution_preflight_policy_digest",
            "execution_envelope_manifest_id",
            "execution_envelope_manifest_digest",
            "execution_envelope_decision_id",
            "execution_envelope_decision_digest",
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
            "rehearsal_evidence_bindings",
            "execution_attempt_id",
            "rehearsal_receipt_ids",
        )
        return {key: deepcopy(data.get(key)) for key in keys}

    def _context(self, run: dict[str, Any]) -> dict[str, Any]:
        if (
            run.get("current_state") != "Complete"
            or run.get("completion_status") != "complete_locked"
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "integration_execution_authorization_review_only requires Complete / complete_locked"
            )
        rehearsal = self.store.load_artifact(
            "production-integration-execution-rehearsal"
        )
        if not rehearsal or rehearsal.get("status") != "locked":
            raise IntegrationExecutionAuthorizationReviewError(
                "locked Iteration 15 execution rehearsal is missing"
            )
        if semantic_digest(rehearsal) != rehearsal.get("content_digest"):
            raise IntegrationExecutionAuthorizationReviewError(
                "locked Iteration 15 execution rehearsal is corrupted"
            )
        rd = rehearsal.get("data") or {}
        if (
            rd.get("execution_rehearsal_schema_version")
            != EXECUTION_REHEARSAL_SCHEMA_VERSION
            or rd.get("execution_rehearsal_policy_version")
            != EXECUTION_REHEARSAL_POLICY_VERSION
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 15 execution rehearsal version unsupported"
            )
        if digest(self._rehearsal_identity(rd)) != rd.get("execution_rehearsal_id"):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 15 execution rehearsal identity is corrupted"
            )
        if (
            rd.get("final_state") != "Complete"
            or rd.get("final_status") != "complete_locked"
            or rd.get("completion_scope")
            != "synthetic_shadow_execution_rehearsal_only"
            or rd.get("synthetic_only") is not True
            or rd.get("real_integration_steps_enabled") != 0
            or rd.get("real_integration_steps_executed") != 0
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 15 execution rehearsal semantics are stale"
            )
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if rd.get(flag) is not False:
                raise IntegrationExecutionAuthorizationReviewError(
                    f"Iteration 15 execution rehearsal cannot authorize {flag}"
                )
        if any(x.get("enabled") is not False for x in rd.get("execution_steps") or []):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 15 real integration steps must remain disabled"
            )

        names = (
            "production-integration-execution-preflight",
            "production-integration-admission",
            "production-integration-plan",
            "production-integration-preflight",
            "readiness-admission",
            "completion",
        )
        artifacts = {name: self.store.load_artifact(name) for name in names}
        for name, artifact in artifacts.items():
            if not artifact or artifact.get("status") != "locked":
                raise IntegrationExecutionAuthorizationReviewError(
                    f"bound upstream artifact {name} is missing"
                )
            if semantic_digest(artifact) != artifact.get("content_digest"):
                raise IntegrationExecutionAuthorizationReviewError(
                    f"bound upstream artifact {name} is corrupted"
                )
        ep = artifacts["production-integration-execution-preflight"]
        admission = artifacts["production-integration-admission"]
        plan = artifacts["production-integration-plan"]
        preflight = artifacts["production-integration-preflight"]
        readiness = artifacts["readiness-admission"]
        completion = artifacts["completion"]
        if (
            ep["data"].get("execution_preflight_schema_version")
            != EXECUTION_PREFLIGHT_SCHEMA_VERSION
            or ep["data"].get("execution_preflight_policy_version")
            != EXECUTION_PREFLIGHT_POLICY_VERSION
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "bound Iteration 14 execution preflight version unsupported"
            )
        if not all(
            (
                rehearsal.get("input_digests") == [ep["content_digest"]],
                ep.get("input_digests") == [admission["content_digest"]],
                admission.get("input_digests") == [plan["content_digest"]],
                plan.get("input_digests") == [preflight["content_digest"]],
                preflight.get("input_digests") == [readiness["content_digest"]],
                readiness.get("input_digests") == [completion["content_digest"]],
            )
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "transitive Iterations 10-15 dependency identity changed"
            )
        pd = plan["data"]
        if not all(
            (
                rd.get("execution_preflight_artifact_digest") == ep["content_digest"],
                rd.get("execution_preflight_id")
                == ep["data"].get("execution_preflight_id"),
                rd.get("admission_artifact_digest") == admission["content_digest"],
                rd.get("admission_id") == admission["data"].get("admission_id"),
                rd.get("plan_artifact_digest") == plan["content_digest"],
                rd.get("plan_id") == pd.get("plan_id"),
                rd.get("plan_graph_digest") == digest(pd.get("plan_steps") or []),
                rd.get("dry_run_assertion_set_digest")
                == digest(pd.get("dry_run_assertion_set") or []),
                rd.get("rollback_boundary_set_digest")
                == digest(pd.get("rollback_boundary_set") or []),
                rd.get("preflight_artifact_digest") == preflight["content_digest"],
                rd.get("preflight_id") == preflight["data"].get("preflight_id"),
                rd.get("readiness_artifact_digest") == readiness["content_digest"],
                rd.get("readiness_assessment_id")
                == readiness["data"].get("assessment_id"),
                rd.get("completion_artifact_digest") == completion["content_digest"],
                rd.get("canonical_chain_digest")
                == completion["data"].get("canonical_chain_digest"),
            )
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 15 bound upstream identity changed"
            )
        final_receipt = self.store.read_json(self.final_receipt_path)
        if (
            not final_receipt
            or digest(final_receipt) != rd.get("final_completion_receipt_digest")
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 9 final completion receipt identity changed"
            )

        steps = pd.get("plan_steps") or []
        if len(steps) != 10 or len({x.get("step_id") for x in steps}) != 10:
            raise IntegrationExecutionAuthorizationReviewError(
                "locked ten-step plan graph is incomplete"
            )
        classification = rd.get("classification")
        if classification not in {"blocked", "rehearsal_complete", "invalid"}:
            raise IntegrationExecutionAuthorizationReviewError(
                "unsupported Iteration 15 rehearsal classification"
            )
        receipts = deepcopy(rd.get("rehearsal_receipts") or [])
        receipt_ids = [x.get("receipt_id") for x in receipts]
        if classification == "rehearsal_complete":
            if (
                len(receipts) != 10
                or rd.get("rehearsal_receipt_count") != 10
                or len(set(receipt_ids)) != 10
                or receipt_ids != rd.get("rehearsal_receipt_ids")
                or [x.get("position") for x in receipts] != list(range(1, 11))
                or [x.get("step_id") for x in receipts]
                != [x.get("step_id") for x in steps]
                or not rd.get("execution_attempt_id")
            ):
                raise IntegrationExecutionAuthorizationReviewError(
                    "Iteration 15 receipt inventory is incomplete, duplicated, or reordered"
                )
            for receipt in receipts:
                if (
                    receipt.get("execution_mode") != "noop"
                    or receipt.get("evaluation_result") != "evaluated_not_executed"
                    or receipt.get("synthetic_only") is not True
                    or receipt.get("external_execution_performed") is not False
                    or receipt.get("real_service_contacted") is not False
                    or receipt.get("side_effect_performed") is not False
                    or receipt.get("production_action_authorized") is not False
                ):
                    raise IntegrationExecutionAuthorizationReviewError(
                        "Iteration 15 receipt substitution is not a synthetic no-op"
                    )
            files = sorted(
                self.store.run_dir.glob("iteration15-rehearsal-receipt-*.json")
            )
            if len(files) != 10:
                raise IntegrationExecutionAuthorizationReviewError(
                    "exact Iteration 15 receipt file inventory is missing"
                )
            for path, expected in zip(files, receipts):
                if self.store.read_json(path) != expected:
                    raise IntegrationExecutionAuthorizationReviewError(
                        "on-disk Iteration 15 receipt differs from locked rehearsal artifact"
                    )
        elif receipts or rd.get("rehearsal_receipt_count") != 0:
            raise IntegrationExecutionAuthorizationReviewError(
                "non-complete Iteration 15 rehearsal cannot carry execution receipts"
            )
        return {
            "execution_rehearsal_artifact_digest": rehearsal["content_digest"],
            "execution_rehearsal_id": rd["execution_rehearsal_id"],
            "rehearsal_classification": classification,
            "rehearsal_reason_codes": deepcopy(
                rd.get("classification_reason_codes") or []
            ),
            "execution_attempt_id": rd.get("execution_attempt_id"),
            "rehearsal_policy_id": rd.get("execution_rehearsal_policy_id"),
            "rehearsal_policy_digest": rd.get("execution_rehearsal_policy_digest"),
            "rehearsal_manifest_id": rd.get("rehearsal_envelope_manifest_id"),
            "rehearsal_manifest_digest": rd.get(
                "rehearsal_envelope_manifest_digest"
            ),
            "rehearsal_decision_id": rd.get("rehearsal_decision_id"),
            "rehearsal_decision_digest": rd.get("rehearsal_decision_digest"),
            "receipt_ids": receipt_ids,
            "receipt_set_digest": digest(receipts),
            "rehearsal_receipts": receipts,
            "execution_preflight_artifact_digest": ep["content_digest"],
            "execution_preflight_id": ep["data"].get("execution_preflight_id"),
            "admission_artifact_digest": admission["content_digest"],
            "admission_id": admission["data"].get("admission_id"),
            "plan_artifact_digest": plan["content_digest"],
            "plan_id": pd.get("plan_id"),
            "plan_graph_digest": digest(steps),
            "plan_steps": deepcopy(steps),
            "dry_run_assertion_set_digest": digest(
                pd.get("dry_run_assertion_set") or []
            ),
            "rollback_boundary_set_digest": digest(
                pd.get("rollback_boundary_set") or []
            ),
            "preflight_artifact_digest": preflight["content_digest"],
            "preflight_id": preflight["data"].get("preflight_id"),
            "readiness_artifact_digest": readiness["content_digest"],
            "readiness_assessment_id": readiness["data"].get("assessment_id"),
            "completion_artifact_digest": completion["content_digest"],
            "final_completion_receipt_digest": rd.get(
                "final_completion_receipt_digest"
            ),
            "canonical_chain_digest": rd.get("canonical_chain_digest"),
            "execution_steps": deepcopy(rd.get("execution_steps") or []),
        }

    def _decision_binding(
        self,
        decision: dict[str, Any] | None,
        manifest_id: str,
        context: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None]:
        if decision is None:
            return {
                "decision_id": None,
                "record_digest": None,
                "decision": None,
            }, "AUTH_REVIEW_DECISION_MISSING"
        required = (
            "record_id",
            "record_kind",
            "decision_id",
            "decision",
            "approved",
            "synthetic_only",
            *self.AUTHORITY_FLAGS,
            "scope",
            "execution_rehearsal_binding_mode",
            "execution_rehearsal_id",
            "authorization_review_manifest_id",
            "review_readiness_only",
            "grants_production_authority",
        )
        missing = [key for key in required if key not in decision]
        if missing:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review decision is ambiguous: missing "
                + ",".join(missing)
            )
        if (
            decision.get("record_kind")
            != "production-integration-execution-authorization-review-decision"
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review decision record_kind unsupported"
            )
        if decision.get("synthetic_only") is not True:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review decision must remain synthetic_only"
            )
        self._assert_authority_false(decision, "authorization-review decision")
        binding = {
            "decision_id": decision.get("decision_id"),
            "record_digest": digest(decision),
            "decision": decision.get("decision"),
        }
        if (
            decision.get("approved") is not True
            or decision.get("decision") != "admit_synthetic_authorization_review"
            or decision.get("scope") != "authorization_review_only"
            or decision.get("execution_rehearsal_binding_mode")
            != "exact_locked_execution_rehearsal_artifact"
            or decision.get("execution_rehearsal_id")
            != context["execution_rehearsal_id"]
            or decision.get("authorization_review_manifest_id") != manifest_id
            or decision.get("review_readiness_only") is not True
            or decision.get("grants_production_authority") is not False
        ):
            return binding, "AUTH_REVIEW_DECISION_NOT_APPROVED"
        return binding, None

    def _validate_evidence(
        self, key: str, record: dict[str, Any], context: dict[str, Any]
    ) -> str | None:
        if (
            not record.get("record_id")
            or record.get("record_kind") != self.EXPECTED_RECORD_KINDS[key]
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                f"{key} authorization-review evidence identity unsupported"
            )
        if record.get("synthetic_only") is not True:
            raise IntegrationExecutionAuthorizationReviewError(
                f"{key} authorization-review evidence is not synthetic-only"
            )
        self._assert_authority_false(record, f"{key} authorization-review evidence")
        if key == "rehearsal_identity":
            if not all(
                (
                    record.get("execution_rehearsal_artifact_digest")
                    == context["execution_rehearsal_artifact_digest"],
                    record.get("execution_rehearsal_id")
                    == context["execution_rehearsal_id"],
                    record.get("execution_attempt_id")
                    == context["execution_attempt_id"],
                    record.get("rehearsal_policy_id")
                    == context["rehearsal_policy_id"],
                    record.get("rehearsal_policy_digest")
                    == context["rehearsal_policy_digest"],
                    record.get("rehearsal_manifest_id")
                    == context["rehearsal_manifest_id"],
                    record.get("rehearsal_manifest_digest")
                    == context["rehearsal_manifest_digest"],
                    record.get("rehearsal_decision_id")
                    == context["rehearsal_decision_id"],
                    record.get("rehearsal_decision_digest")
                    == context["rehearsal_decision_digest"],
                )
            ):
                raise IntegrationExecutionAuthorizationReviewError(
                    "authorization-review rehearsal identity binding changed"
                )
        elif key == "receipt_inventory":
            if (
                record.get("receipt_count") != 10
                or record.get("receipt_ids") != context["receipt_ids"]
                or record.get("receipt_set_digest") != context["receipt_set_digest"]
            ):
                raise IntegrationExecutionAuthorizationReviewError(
                    "authorization-review receipt inventory changed"
                )
        elif key == "receipt_verification":
            if (
                record.get("required") is not True
                or record.get("verify_exact_order") is not True
                or record.get("verify_noop_and_side_effect_free") is not True
                or record.get("reject_real_service_substitution") is not True
                or record.get("receipt_set_digest") != context["receipt_set_digest"]
            ):
                return "AUTH_REVIEW_RECEIPT_VERIFICATION_UNSAFE"
        elif key == "executor_review_contract":
            if (
                record.get("executor_contract_id")
                != "synthetic-review-only-executor-contract"
                or record.get("executor_contract_version") != "1.0.0"
                or record.get("real_executor_present") is not False
                or record.get("executable") is not False
            ):
                return "AUTH_REVIEW_EXECUTOR_CONTRACT_UNSAFE"
        elif key == "step_selection_scope":
            if (
                record.get("plan_id") != context["plan_id"]
                or record.get("plan_graph_digest") != context["plan_graph_digest"]
                or record.get("step_ids")
                != [x.get("step_id") for x in context["plan_steps"]]
            ):
                raise IntegrationExecutionAuthorizationReviewError(
                    "authorization-review step scope changed"
                )
        elif key == "target_environment":
            if (
                record.get("target_environment_id")
                != "synthetic-shadow-authorization-review"
                or record.get("environment_class") != "synthetic_nonproduction"
                or record.get("production_target") is not False
                or record.get("real_target_contact_authorized") is not False
            ):
                return "AUTH_REVIEW_TARGET_ENVIRONMENT_NOT_SYNTHETIC"
        elif key == "credential_use_policy":
            if (
                record.get("policy_id") != "no-credentials-authorization-review-v1"
                or record.get("credentials_present") is not False
                or record.get("credential_access_required") is not False
                or record.get("credential_use_allowed") is not False
            ):
                return "AUTH_REVIEW_CREDENTIAL_POLICY_UNSAFE"
        elif key == "rollback_recovery_policy":
            if (
                record.get("rollback_boundary_set_digest")
                != context["rollback_boundary_set_digest"]
                or record.get("review_required") is not True
                or record.get("rollback_execution_authorized") is not False
            ):
                return "AUTH_REVIEW_ROLLBACK_POLICY_UNSAFE"
        elif key == "pre_execution_verification_review":
            if (
                not record.get("verification_policy_id")
                or record.get("required") is not True
                or record.get("approved_for_real_execution") is not False
            ):
                return "AUTH_REVIEW_PRE_EXECUTION_VERIFICATION_UNSAFE"
        elif key == "stop_abort_conditions":
            if (
                not record.get("policy_id")
                or not record.get("stop_conditions")
                or record.get("abort_on_identity_mismatch") is not True
                or record.get("abort_on_receipt_mismatch") is not True
                or record.get("abort_on_authority_flag") is not True
                or record.get("abort_on_cost_guard_failure") is not True
            ):
                return "AUTH_REVIEW_STOP_ABORT_CONDITIONS_INCOMPLETE"
        elif key == "cutover_decommission_state":
            if (
                record.get("cutover_authorized") is not False
                or record.get("legacy_decommission_authorized") is not False
                or record.get("readers_routed_to_greenfield") is not False
                or record.get("production_publication") is not False
            ):
                return "AUTH_REVIEW_CUTOVER_OR_DECOMMISSION_AUTHORIZED"
        elif key == "zero_incremental_cost":
            required = (
                "approved",
                "zero_incremental_cost",
                "separately_billed_openai_api_required",
                "paid_completion_or_storage_api_required",
                "paid_deployment_or_hosting_api_required",
                "other_incremental_paid_dependency_required",
            )
            if any(field not in record for field in required):
                raise IntegrationExecutionAuthorizationReviewError(
                    "authorization-review zero-cost evidence ambiguous"
                )
            if (
                record.get("approved") is not True
                or record.get("zero_incremental_cost") is not True
                or any(record.get(field) is not False for field in required[2:])
            ):
                return "AUTH_REVIEW_ZERO_INCREMENTAL_COST_GUARD_FAILED"
        return None

    def _evaluate(
        self, context: dict[str, Any], policy: dict[str, Any], manifest: dict[str, Any]
    ) -> dict[str, Any]:
        bindings: dict[str, Any] = {}
        if context["rehearsal_classification"] == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION15_EXECUTION_REHEARSAL_INVALID",
                    *context["rehearsal_reason_codes"],
                ],
                "authorization_review_evidence_bindings": bindings,
                "authorization_review_decision_binding": {
                    "decision_id": None,
                    "record_digest": None,
                    "decision": None,
                },
            }
        if context["rehearsal_classification"] == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION15_EXECUTION_REHEARSAL_BLOCKED",
                    *context["rehearsal_reason_codes"],
                ],
                "authorization_review_evidence_bindings": bindings,
                "authorization_review_decision_binding": {
                    "decision_id": None,
                    "record_digest": None,
                    "decision": None,
                },
            }
        if context["rehearsal_classification"] != "rehearsal_complete":
            raise IntegrationExecutionAuthorizationReviewError(
                "unsupported Iteration 15 rehearsal classification"
            )
        blocking: list[str] = []
        for key in self.REQUIRED_EVIDENCE:
            record = manifest["evidence"][key]
            if record is None:
                bindings[key] = {"record_id": None, "record_digest": None}
                blocking.append(self.MISSING_REASON_CODES[key])
                continue
            reason = self._validate_evidence(key, record, context)
            bindings[key] = {
                "record_id": record["record_id"],
                "record_digest": digest(record),
            }
            if reason:
                blocking.append(reason)
        decision_binding, decision_reason = self._decision_binding(
            manifest.get("authorization_review_decision"),
            manifest["manifest_id"],
            context,
        )
        if decision_reason:
            blocking.append(decision_reason)
        if blocking:
            classification = "blocked"
            reasons = blocking
        else:
            classification = "authorization_review_ready"
            reasons = [policy["authorization_review_ready_reason_code"]]
        return {
            "classification": classification,
            "classification_reason_codes": reasons,
            "authorization_review_evidence_bindings": bindings,
            "authorization_review_decision_binding": decision_binding,
        }

    def _new_state(self, input_identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": input_identity,
            "attempts": {
                "evaluation": 0,
                "artifact_assembly": 0,
                "receipt_verifications": {},
            },
            "evaluation": None,
            "verification_digests": {},
            "metrics": {
                "validation_checks": 0,
                "evaluation_attempts": 0,
                "evaluation_reuse": 0,
                "receipt_verification_attempts": 0,
                "receipt_verification_reuse": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "recovery_attempts": 0,
                "blocked_classifications": 0,
                "authorization_review_ready_classifications": 0,
                "invalid_classifications": 0,
                "elapsed_ms": 0,
                "anti_rework": {
                    "locked_iterations_1_15_reexecution": 0,
                    "iteration15_execution_rehearsal_reevaluation": 0,
                    "iteration15_execution_rehearsal_rebuild": 0,
                    "full_pipeline_restarts": 0,
                },
            },
        }

    def _load_state(
        self, input_identity: dict[str, Any] | None = None, *, optional: bool = False
    ) -> dict[str, Any] | None:
        state = self.store.read_json(self.state_path)
        if state is None:
            if optional:
                return None
            if input_identity is None:
                raise IntegrationExecutionAuthorizationReviewError(
                    "authorization-review state input identity required"
                )
            return self._new_state(input_identity)
        if (
            state.get("schema_version") != EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "Iteration 16 authorization-review state is stale or incompatible"
            )
        if input_identity is not None and state.get("input_identity") != input_identity:
            raise IntegrationExecutionAuthorizationReviewError(
                "cached authorization-review state binds different identities"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                **deepcopy(state["metrics"]),
                "attempts": deepcopy(state["attempts"]),
            },
        )

    def _record_incident(
        self, boundary_id: str, message: str, state: dict[str, Any]
    ) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION,
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
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization-review recovery incident identity changed"
            )
        incident["result"] = "recovered"
        incident["recovery_receipt"] = {
            "boundary_id": incident["boundary_id"],
            "input_identity": deepcopy(state["input_identity"]),
            "result": "recovered",
            "recovered_at": utc_now(),
        }
        state["metrics"]["recovery_attempts"] += 1
        self.store._atomic_write(self.incident_path, incident)

    def _verification_path(self, position: int, step_id: str) -> Path:
        safe = re.sub(r"[^a-z0-9-]+", "-", step_id.lower()).strip("-")
        return self.store.run_dir / (
            f"iteration16-authorization-review-receipt-verification-"
            f"{position:02d}-{safe}.json"
        )

    def _verification_data(
        self, context: dict[str, Any], position: int, receipt: dict[str, Any]
    ) -> dict[str, Any]:
        body = {
            "schema_version": EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION,
            "execution_rehearsal_id": context["execution_rehearsal_id"],
            "execution_attempt_id": context["execution_attempt_id"],
            "position": position,
            "step_id": receipt["step_id"],
            "receipt_id": receipt["receipt_id"],
            "receipt_digest": digest(receipt),
            "receipt_set_digest": context["receipt_set_digest"],
            "synthetic_only": True,
            "noop_verified": True,
            "side_effect_free_verified": True,
            "real_service_contacted": False,
            "external_execution_performed": False,
            "real_executor_invocation_authorized": False,
            "credentials_use_authorized": False,
            "production_action_authorized": False,
        }
        return {**body, "verification_id": digest(body)}

    def _ensure_receipt_verifications(
        self, context: dict[str, Any], evaluated: dict[str, Any], state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if evaluated["classification"] != "authorization_review_ready":
            return []
        result: list[dict[str, Any]] = []
        for position, receipt in enumerate(context["rehearsal_receipts"], 1):
            step_id = receipt["step_id"]
            path = self._verification_path(position, step_id)
            expected = self._verification_data(context, position, receipt)
            existing = self.store.read_json(path)
            state["attempts"]["receipt_verifications"].setdefault(step_id, 0)
            if existing is not None:
                if existing != expected:
                    raise IntegrationExecutionAuthorizationReviewError(
                        f"cached receipt verification identity changed for {step_id}"
                    )
                state["metrics"]["receipt_verification_reuse"] += 1
                state["verification_digests"][step_id] = digest(existing)
                result.append(existing)
                continue
            state["attempts"]["receipt_verifications"][step_id] += 1
            state["metrics"]["receipt_verification_attempts"] += 1
            self._save_state(state)
            boundary = f"receipt:{step_id}"
            if self.failure_boundary_id == boundary and not self._failure_fired:
                self._failure_fired = True
                self._record_incident(boundary, self.failure_class, state)
                self._write_metrics(state)
                raise IntegrationExecutionAuthorizationReviewBoundaryFailure(
                    "authorization_review_receipt_verification",
                    boundary,
                    self.failure_class,
                )
            self.store._atomic_write(path, expected)
            state["verification_digests"][step_id] = digest(expected)
            result.append(expected)
            self._save_state(state)
        if len(result) != 10:
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization_review_ready requires exactly ten receipt verifications"
            )
        return result

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        context = self._context(run)
        policy, manifest = self._policy_and_manifest()
        decision = manifest.get("authorization_review_decision")
        input_identity = {
            "execution_rehearsal_artifact_digest": context[
                "execution_rehearsal_artifact_digest"
            ],
            "execution_rehearsal_id": context["execution_rehearsal_id"],
            "authorization_review_policy_digest": digest(policy),
            "authorization_review_manifest_digest": digest(manifest),
            "authorization_review_decision_id": (
                decision.get("decision_id") if decision else None
            ),
            "authorization_review_decision_digest": (
                digest(decision) if decision else None
            ),
        }
        state = self._load_state(input_identity)
        state["metrics"]["validation_checks"] += 1
        if state.get("evaluation") is None:
            state["attempts"]["evaluation"] += 1
            state["metrics"]["evaluation_attempts"] += 1
            self._save_state(state)
            if self.failure_boundary_id == "evaluation" and not self._failure_fired:
                self._failure_fired = True
                self._record_incident("evaluation", self.failure_class, state)
                self._write_metrics(state)
                raise IntegrationExecutionAuthorizationReviewBoundaryFailure(
                    "authorization_review_evaluation",
                    "evaluation",
                    self.failure_class,
                )
            outcome = self._evaluate(context, policy, manifest)
            state["evaluation"] = {
                **deepcopy(context),
                **outcome,
                "input_identity": input_identity,
                "authorization_review_policy_version": policy[
                    "authorization_review_policy_version"
                ],
                "authorization_review_policy_id": policy["policy_id"],
                "authorization_review_manifest_id": manifest["manifest_id"],
            }
        else:
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        verifications = self._ensure_receipt_verifications(context, evaluated, state)
        evaluated["receipt_verifications"] = verifications
        state["evaluation"]["verification_ids"] = [
            x["verification_id"] for x in verifications
        ]
        state["metrics"]["elapsed_ms"] = max(
            0, int((time.monotonic() - started) * 1000)
        )
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
        return evaluated

    def _artifact_data(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        decision = evaluated["authorization_review_decision_binding"]
        identity = {
            "authorization_review_schema_version": EXECUTION_AUTHORIZATION_REVIEW_SCHEMA_VERSION,
            "authorization_review_policy_version": evaluated[
                "authorization_review_policy_version"
            ],
            "authorization_review_policy_id": evaluated[
                "authorization_review_policy_id"
            ],
            "authorization_review_policy_digest": evaluated["input_identity"][
                "authorization_review_policy_digest"
            ],
            "authorization_review_manifest_id": evaluated[
                "authorization_review_manifest_id"
            ],
            "authorization_review_manifest_digest": evaluated["input_identity"][
                "authorization_review_manifest_digest"
            ],
            "authorization_review_decision_id": decision.get("decision_id"),
            "authorization_review_decision_digest": decision.get("record_digest"),
            "execution_rehearsal_artifact_digest": evaluated[
                "execution_rehearsal_artifact_digest"
            ],
            "execution_rehearsal_id": evaluated["execution_rehearsal_id"],
            "rehearsal_classification": evaluated["rehearsal_classification"],
            "rehearsal_reason_codes": evaluated["rehearsal_reason_codes"],
            "execution_attempt_id": evaluated["execution_attempt_id"],
            "rehearsal_policy_id": evaluated["rehearsal_policy_id"],
            "rehearsal_policy_digest": evaluated["rehearsal_policy_digest"],
            "rehearsal_manifest_id": evaluated["rehearsal_manifest_id"],
            "rehearsal_manifest_digest": evaluated["rehearsal_manifest_digest"],
            "rehearsal_decision_id": evaluated["rehearsal_decision_id"],
            "rehearsal_decision_digest": evaluated["rehearsal_decision_digest"],
            "rehearsal_receipt_ids": evaluated["receipt_ids"],
            "rehearsal_receipt_set_digest": evaluated["receipt_set_digest"],
            "receipt_verification_ids": [
                x["verification_id"] for x in evaluated["receipt_verifications"]
            ],
            "execution_preflight_artifact_digest": evaluated[
                "execution_preflight_artifact_digest"
            ],
            "execution_preflight_id": evaluated["execution_preflight_id"],
            "admission_artifact_digest": evaluated["admission_artifact_digest"],
            "admission_id": evaluated["admission_id"],
            "plan_artifact_digest": evaluated["plan_artifact_digest"],
            "plan_id": evaluated["plan_id"],
            "plan_graph_digest": evaluated["plan_graph_digest"],
            "dry_run_assertion_set_digest": evaluated[
                "dry_run_assertion_set_digest"
            ],
            "rollback_boundary_set_digest": evaluated[
                "rollback_boundary_set_digest"
            ],
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
            "classification_reason_codes": evaluated[
                "classification_reason_codes"
            ],
            "authorization_review_evidence_bindings": evaluated[
                "authorization_review_evidence_bindings"
            ],
        }
        return {
            **identity,
            "authorization_review_id": digest(identity),
            "receipt_verifications": deepcopy(evaluated["receipt_verifications"]),
            "receipt_verification_count": len(evaluated["receipt_verifications"]),
            "execution_steps": deepcopy(evaluated["execution_steps"]),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_execution_authorization_review_only",
            "synthetic_only": True,
            "production_action_authorized": False,
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "production_publication": False,
            "real_executor_invocation_authorized": False,
            "credentials_use_authorized": False,
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
            raise IntegrationExecutionAuthorizationReviewBoundaryFailure(
                "authorization_review_validation",
                "authorization_review_artifact",
                "cached authorization-review artifact is not valid and locked",
            )
        if existing.get("data") != self._artifact_data(run, evaluated):
            raise IntegrationExecutionAuthorizationReviewBoundaryFailure(
                "authorization_review_validation",
                "authorization_review_artifact",
                "cached authorization-review artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_authorization_review(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id == "final_authorization_review_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._record_incident(
                "final_authorization_review_artifact", self.failure_class, state
            )
            self._write_metrics(state)
            raise IntegrationExecutionAuthorizationReviewBoundaryFailure(
                "authorization_review_artifact_assembly",
                "final_authorization_review_artifact",
                self.failure_class,
            )
        return self._artifact_data(run, evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionAuthorizationReviewError(
                "final authorization-review artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionAuthorizationReviewError(
                "final authorization-review artifact digest invalid"
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
                raise IntegrationExecutionAuthorizationReviewError(
                    f"authorization review cannot authorize/mutate {flag}"
                )
        if (
            data.get("real_integration_steps_enabled") != 0
            or data.get("real_integration_steps_executed") != 0
        ):
            raise IntegrationExecutionAuthorizationReviewError(
                "authorization review cannot enable or execute real steps"
            )
        if any(x.get("enabled") is not False for x in data.get("execution_steps") or []):
            raise IntegrationExecutionAuthorizationReviewError(
                "all real integration-plan steps must remain disabled"
            )
        classification = data.get("classification")
        if classification == "authorization_review_ready":
            if data.get("rehearsal_classification") != "rehearsal_complete":
                raise IntegrationExecutionAuthorizationReviewError(
                    "only rehearsal_complete can become authorization_review_ready"
                )
            if not data.get("authorization_review_decision_id"):
                raise IntegrationExecutionAuthorizationReviewError(
                    "authorization_review_ready requires separate review decision"
                )
            if (
                data.get("receipt_verification_count") != 10
                or len(data.get("receipt_verifications") or []) != 10
            ):
                raise IntegrationExecutionAuthorizationReviewError(
                    "authorization_review_ready requires ten receipt verifications"
                )
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionAuthorizationReviewError(
                "unsupported authorization-review classification"
            )
        state = self._load_state()
        if classification == "blocked":
            state["metrics"]["blocked_classifications"] += 1
        elif classification == "authorization_review_ready":
            state["metrics"]["authorization_review_ready_classifications"] += 1
        else:
            state["metrics"]["invalid_classifications"] += 1
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
