from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_SCHEMA_VERSION,
    EXECUTION_PREFLIGHT_POLICY_VERSION,
    EXECUTION_PREFLIGHT_SCHEMA_VERSION,
    PLAN_POLICY_VERSION,
    PLAN_SCHEMA_VERSION,
    PREFLIGHT_POLICY_VERSION,
    PREFLIGHT_SCHEMA_VERSION,
    READINESS_POLICY_VERSION,
    READINESS_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class IntegrationExecutionPreflightError(ContractError):
    pass


class IntegrationExecutionPreflightBoundaryFailure(IntegrationExecutionPreflightError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"execution_preflight:{boundary_id}"


class ProductionIntegrationExecutionPreflight:
    """Deterministic, non-mutating Iteration 14 execution-preflight gate."""

    REQUIRED_EVIDENCE = (
        "executor_contract",
        "step_selection_scope",
        "step_enablement",
        "dry_run_assertions",
        "rollback_restore",
        "target_environment",
        "pre_execution_verification",
        "stop_abort_conditions",
        "cutover_decommission_state",
        "zero_incremental_cost",
    )

    MISSING_REASON_CODES = {
        "executor_contract": "EXECUTION_EXECUTOR_CONTRACT_MISSING",
        "step_selection_scope": "EXECUTION_STEP_SELECTION_SCOPE_MISSING",
        "step_enablement": "EXECUTION_STEP_ENABLEMENT_MISSING",
        "dry_run_assertions": "EXECUTION_DRY_RUN_BINDING_MISSING",
        "rollback_restore": "EXECUTION_ROLLBACK_RESTORE_BINDING_MISSING",
        "target_environment": "EXECUTION_TARGET_ENVIRONMENT_MISSING",
        "pre_execution_verification": "EXECUTION_PRE_EXECUTION_VERIFICATION_MISSING",
        "stop_abort_conditions": "EXECUTION_STOP_ABORT_CONDITIONS_MISSING",
        "cutover_decommission_state": "EXECUTION_CUTOVER_DECOMMISSION_STATE_MISSING",
        "zero_incremental_cost": "EXECUTION_ZERO_INCREMENTAL_COST_GUARD_MISSING",
    }

    EXPECTED_RECORD_KINDS = {
        "executor_contract": "production-integration-executor-contract",
        "step_selection_scope": "production-integration-step-selection-scope",
        "step_enablement": "production-integration-step-enablement",
        "dry_run_assertions": "production-integration-dry-run-binding",
        "rollback_restore": "production-integration-rollback-restore-binding",
        "target_environment": "production-integration-target-environment",
        "pre_execution_verification": "production-integration-pre-execution-verification-policy",
        "stop_abort_conditions": "production-integration-stop-abort-policy",
        "cutover_decommission_state": "production-integration-cutover-decommission-state",
        "zero_incremental_cost": "cost-policy-approval",
    }

    EXPLICIT_REFERENCE_FIELDS = (
        "executor_contract_id",
        "executor_contract_version",
        "plan_id",
        "plan_graph_digest",
        "step_ids",
        "steps",
        "dry_run_assertion_set_digest",
        "rollback_boundary_set_digest",
        "restore_point_id",
        "rollback_execution_authorized",
        "target_environment_id",
        "environment_class",
        "production_target",
        "verification_policy_id",
        "required",
        "approved_for_execution",
        "policy_id",
        "stop_conditions",
        "abort_on_identity_mismatch",
        "abort_on_cost_guard_failure",
        "cutover_authorized",
        "legacy_decommission_authorized",
        "readers_routed_to_greenfield",
        "approved",
        "zero_incremental_cost",
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
        failure_class: str = "synthetic_integration_execution_preflight_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("execution_preflight:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration14-execution-preflight-state.json"
        self.metrics_path = self.store.run_dir / "iteration14-execution-preflight-metrics.json"
        self.incident_path = self.store.run_dir / "iteration14-execution-preflight-incident.json"
        self.final_receipt_path = self.store.run_dir / "iteration9-final-completion-receipt.json"

    def _read_json_fixture(self, name: str) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionPreflightError(
                "production integration execution preflight is repository-evidence-only and "
                "fail-closed: no approved production execution envelope is configured"
            )
        path = self.fixture_root / name
        if not path.exists():
            raise IntegrationExecutionPreflightError(
                f"missing Iteration 14 execution-preflight fixture: {path}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _policy_and_manifest(self) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self._read_json_fixture("execution-preflight-policy.json")
        manifest = self._read_json_fixture("execution-envelope-manifest.json")
        if (
            policy.get("schema_version") != EXECUTION_PREFLIGHT_SCHEMA_VERSION
            or policy.get("execution_preflight_policy_version")
            != EXECUTION_PREFLIGHT_POLICY_VERSION
        ):
            raise IntegrationExecutionPreflightError(
                "unsupported Iteration 14 execution-preflight policy/schema version"
            )
        if policy.get("policy_id") != "production-integration-execution-preflight-v1":
            raise IntegrationExecutionPreflightError(
                "unsupported Iteration 14 execution-preflight policy identity"
            )
        if policy.get("synthetic_only") is not True:
            raise IntegrationExecutionPreflightError(
                "Iteration 14 execution-preflight policy must remain synthetic_only"
            )
        if policy.get("production_action_authorized") is not False:
            raise IntegrationExecutionPreflightError(
                "Iteration 14 execution-preflight policy cannot authorize production action"
            )
        if policy.get("require_exact_admission_binding") is not True:
            raise IntegrationExecutionPreflightError(
                "execution-preflight policy must require exact locked admission binding"
            )
        if policy.get("require_separate_execution_envelope_decision") is not True:
            raise IntegrationExecutionPreflightError(
                "execution-preflight policy must require a separate execution-envelope decision"
            )
        if policy.get("require_all_real_steps_disabled") is not True:
            raise IntegrationExecutionPreflightError(
                "execution-preflight policy must require all real integration steps disabled"
            )
        if tuple(policy.get("required_evidence") or ()) != self.REQUIRED_EVIDENCE:
            raise IntegrationExecutionPreflightError(
                "execution-envelope evidence inventory is incomplete or ambiguous"
            )
        if policy.get("classifications") != ["blocked", "execution_review_ready", "invalid"]:
            raise IntegrationExecutionPreflightError(
                "execution-preflight classification policy is unsupported"
            )

        if (
            manifest.get("schema_version") != EXECUTION_PREFLIGHT_SCHEMA_VERSION
            or manifest.get("execution_envelope_manifest_version") != "1.0.0"
        ):
            raise IntegrationExecutionPreflightError(
                "unsupported Iteration 14 execution-envelope manifest version"
            )
        if manifest.get("synthetic_only") is not True:
            raise IntegrationExecutionPreflightError(
                "execution-envelope manifest must remain synthetic_only"
            )
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if manifest.get(flag) is not False:
                raise IntegrationExecutionPreflightError(
                    f"execution-envelope manifest cannot authorize {flag}"
                )
        closure = manifest.get("iteration13_closure") or {}
        if (
            closure.get("repository_closure_status") != "complete"
            or closure.get("iteration14_ready") is not True
            or closure.get("evidence_path")
            != "evidence/iteration13/synthetic-shadow-production-integration-admission-evidence.json"
        ):
            raise IntegrationExecutionPreflightError(
                "Iteration 13 operational closure is incomplete or untrusted"
            )
        binding = manifest.get("admission_binding") or {}
        if binding != {
            "binding_type": "exact_locked_admission_artifact",
            "artifact_type": "production-integration-admission",
            "admission_id_field": "data.admission_id",
            "artifact_digest_field": "content_digest",
        }:
            raise IntegrationExecutionPreflightError(
                "execution-envelope exact-admission binding declaration is invalid"
            )
        evidence = manifest.get("evidence")
        if not isinstance(evidence, dict) or tuple(evidence.keys()) != self.REQUIRED_EVIDENCE:
            raise IntegrationExecutionPreflightError(
                "execution-envelope evidence inventory is incomplete or ambiguous"
            )
        decision = manifest.get("execution_envelope_decision")
        if decision is not None and not isinstance(decision, dict):
            raise IntegrationExecutionPreflightError(
                "execution-envelope decision must be an explicit repository record or null"
            )
        return policy, manifest

    def _admission_context(self, run: dict[str, Any]) -> dict[str, Any]:
        if run.get("current_state") != "Complete" or run.get("completion_status") != "complete_locked":
            raise IntegrationExecutionPreflightError(
                "integration_execution_preflight_only requires Complete / complete_locked"
            )
        admission = self.store.load_artifact("production-integration-admission")
        if not admission or admission.get("status") != "locked":
            raise IntegrationExecutionPreflightError(
                "locked Iteration 13 production-integration admission is missing"
            )
        if semantic_digest(admission) != admission.get("content_digest"):
            raise IntegrationExecutionPreflightError(
                "locked Iteration 13 production-integration admission is corrupted"
            )
        data = admission.get("data") or {}
        if (
            data.get("admission_schema_version") != ADMISSION_SCHEMA_VERSION
            or data.get("admission_policy_version") != ADMISSION_POLICY_VERSION
        ):
            raise IntegrationExecutionPreflightError(
                "Iteration 13 admission schema/policy version is unsupported"
            )
        if (
            data.get("final_state") != "Complete"
            or data.get("final_status") != "complete_locked"
            or data.get("completion_scope") != "synthetic_shadow_admission_only"
            or data.get("synthetic_only") is not True
        ):
            raise IntegrationExecutionPreflightError(
                "Iteration 13 admission semantics are stale or unsafe"
            )
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if data.get(flag) is not False:
                raise IntegrationExecutionPreflightError(
                    f"Iteration 13 admission cannot authorize {flag}"
                )

        semantic_identity = {
            "admission_schema_version": data.get("admission_schema_version"),
            "admission_policy_version": data.get("admission_policy_version"),
            "admission_policy_id": data.get("admission_policy_id"),
            "admission_policy_digest": data.get("admission_policy_digest"),
            "admission_manifest_id": data.get("admission_manifest_id"),
            "admission_manifest_digest": data.get("admission_manifest_digest"),
            "plan_artifact_digest": data.get("plan_artifact_digest"),
            "plan_id": data.get("plan_id"),
            "plan_schema_version": data.get("plan_schema_version"),
            "plan_policy_version": data.get("plan_policy_version"),
            "plan_policy_id": data.get("plan_policy_id"),
            "plan_policy_digest": data.get("plan_policy_digest"),
            "plan_classification": data.get("plan_classification"),
            "plan_reason_codes": data.get("plan_reason_codes"),
            "plan_graph_digest": data.get("plan_graph_digest"),
            "dry_run_assertion_set_digest": data.get("dry_run_assertion_set_digest"),
            "rollback_boundary_set_digest": data.get("rollback_boundary_set_digest"),
            "preflight_artifact_digest": data.get("preflight_artifact_digest"),
            "preflight_id": data.get("preflight_id"),
            "readiness_artifact_digest": data.get("readiness_artifact_digest"),
            "readiness_assessment_id": data.get("readiness_assessment_id"),
            "completion_artifact_digest": data.get("completion_artifact_digest"),
            "final_completion_receipt_digest": data.get("final_completion_receipt_digest"),
            "canonical_chain_digest": data.get("canonical_chain_digest"),
            "classification": data.get("classification"),
            "classification_reason_codes": data.get("classification_reason_codes"),
            "evidence_bindings": data.get("evidence_bindings"),
            "admission_decision_id": data.get("admission_decision_id"),
            "admission_decision_digest": data.get("admission_decision_digest"),
        }
        if digest(semantic_identity) != data.get("admission_id"):
            raise IntegrationExecutionPreflightError("Iteration 13 admission identity is corrupted")
        classification = data.get("classification")
        if classification not in {"blocked", "authorization_ready", "invalid"}:
            raise IntegrationExecutionPreflightError(
                "unsupported Iteration 13 admission classification"
            )

        plan = self.store.load_artifact("production-integration-plan")
        preflight = self.store.load_artifact("production-integration-preflight")
        readiness = self.store.load_artifact("readiness-admission")
        completion = self.store.load_artifact("completion")
        for name, artifact in (
            ("production-integration-plan", plan),
            ("production-integration-preflight", preflight),
            ("readiness-admission", readiness),
            ("completion", completion),
        ):
            if not artifact or artifact.get("status") != "locked":
                raise IntegrationExecutionPreflightError(
                    f"bound upstream artifact {name} is missing"
                )
            if semantic_digest(artifact) != artifact.get("content_digest"):
                raise IntegrationExecutionPreflightError(
                    f"bound upstream artifact {name} is corrupted"
                )

        plan_data = plan["data"]
        preflight_data = preflight["data"]
        readiness_data = readiness["data"]
        completion_data = completion["data"]
        if (
            plan_data.get("plan_schema_version") != PLAN_SCHEMA_VERSION
            or plan_data.get("plan_policy_version") != PLAN_POLICY_VERSION
            or preflight_data.get("preflight_schema_version") != PREFLIGHT_SCHEMA_VERSION
            or preflight_data.get("preflight_policy_version") != PREFLIGHT_POLICY_VERSION
            or readiness_data.get("readiness_schema_version") != READINESS_SCHEMA_VERSION
            or readiness_data.get("readiness_policy_version") != READINESS_POLICY_VERSION
        ):
            raise IntegrationExecutionPreflightError(
                "bound upstream schema/policy version is unsupported"
            )
        plan_semantic_identity = {
            "plan_schema_version": plan_data.get("plan_schema_version"),
            "plan_policy_version": plan_data.get("plan_policy_version"),
            "plan_policy_id": plan_data.get("plan_policy_id"),
            "plan_policy_digest": plan_data.get("plan_policy_digest"),
            "preflight_artifact_digest": plan_data.get("preflight_artifact_digest"),
            "preflight_id": plan_data.get("preflight_id"),
            "preflight_schema_version": plan_data.get("preflight_schema_version"),
            "preflight_policy_version": plan_data.get("preflight_policy_version"),
            "preflight_classification": plan_data.get("preflight_classification"),
            "resolution_manifest_digest": plan_data.get("resolution_manifest_digest"),
            "readiness_artifact_digest": plan_data.get("readiness_artifact_digest"),
            "readiness_assessment_id": plan_data.get("readiness_assessment_id"),
            "completion_artifact_digest": plan_data.get("completion_artifact_digest"),
            "final_completion_receipt_digest": plan_data.get("final_completion_receipt_digest"),
            "canonical_chain_digest": plan_data.get("canonical_chain_digest"),
            "classification": plan_data.get("classification"),
            "classification_reason_codes": plan_data.get("classification_reason_codes"),
            "plan_steps": plan_data.get("plan_steps"),
            "dry_run_assertion_set": plan_data.get("dry_run_assertion_set"),
            "rollback_boundary_set": plan_data.get("rollback_boundary_set"),
        }
        if digest(plan_semantic_identity) != plan_data.get("plan_id"):
            raise IntegrationExecutionPreflightError("Iteration 12 plan identity is corrupted")

        if admission.get("input_digests") != [plan.get("content_digest")]:
            raise IntegrationExecutionPreflightError(
                "Iteration 13 admission dependency identity changed"
            )
        if plan.get("input_digests") != [preflight.get("content_digest")]:
            raise IntegrationExecutionPreflightError(
                "Iteration 12 plan dependency identity changed"
            )
        if preflight.get("input_digests") != [readiness.get("content_digest")]:
            raise IntegrationExecutionPreflightError(
                "Iteration 11 preflight dependency identity changed"
            )
        if readiness.get("input_digests") != [completion.get("content_digest")]:
            raise IntegrationExecutionPreflightError(
                "Iteration 10 readiness dependency identity changed"
            )
        exact_checks = (
            (data.get("plan_artifact_digest"), plan.get("content_digest")),
            (data.get("plan_id"), plan_data.get("plan_id")),
            (data.get("plan_graph_digest"), digest(plan_data.get("plan_steps") or [])),
            (
                data.get("dry_run_assertion_set_digest"),
                digest(plan_data.get("dry_run_assertion_set") or []),
            ),
            (
                data.get("rollback_boundary_set_digest"),
                digest(plan_data.get("rollback_boundary_set") or []),
            ),
            (data.get("preflight_artifact_digest"), preflight.get("content_digest")),
            (data.get("preflight_id"), preflight_data.get("preflight_id")),
            (data.get("readiness_artifact_digest"), readiness.get("content_digest")),
            (data.get("readiness_assessment_id"), readiness_data.get("assessment_id")),
            (data.get("completion_artifact_digest"), completion.get("content_digest")),
        )
        if any(left != right for left, right in exact_checks):
            raise IntegrationExecutionPreflightError(
                "Iteration 13 admission bound upstream identity changed"
            )
        final_receipt = self.store.read_json(self.final_receipt_path)
        if (
            not final_receipt
            or digest(final_receipt) != data.get("final_completion_receipt_digest")
            or readiness_data.get("final_completion_receipt_digest")
            != data.get("final_completion_receipt_digest")
        ):
            raise IntegrationExecutionPreflightError(
                "bound Iteration 9 final completion receipt identity changed"
            )
        if not (
            data.get("canonical_chain_digest")
            == readiness_data.get("canonical_chain_digest")
            == completion_data.get("canonical_chain_digest")
        ):
            raise IntegrationExecutionPreflightError(
                "bound canonical-chain identity changed"
            )

        steps = plan_data.get("plan_steps") or []
        assertions = plan_data.get("dry_run_assertion_set") or []
        rollbacks = plan_data.get("rollback_boundary_set") or []
        if len(steps) != 10 or len({x.get("step_id") for x in steps}) != 10:
            raise IntegrationExecutionPreflightError(
                "Iteration 12 plan graph identity is incomplete or ambiguous"
            )
        return {
            "admission_artifact_digest": admission["content_digest"],
            "admission_id": data["admission_id"],
            "admission_schema_version": data["admission_schema_version"],
            "admission_policy_version": data["admission_policy_version"],
            "admission_classification": classification,
            "admission_reason_codes": deepcopy(data.get("classification_reason_codes") or []),
            "admission_evidence_binding_digest": digest(data.get("evidence_bindings") or {}),
            "admission_decision_id": data.get("admission_decision_id"),
            "admission_decision_digest": data.get("admission_decision_digest"),
            "plan_artifact_digest": plan["content_digest"],
            "plan_id": plan_data["plan_id"],
            "plan_graph_digest": digest(steps),
            "dry_run_assertion_set_digest": digest(assertions),
            "rollback_boundary_set_digest": digest(rollbacks),
            "plan_steps": deepcopy(steps),
            "dry_run_assertion_set": deepcopy(assertions),
            "rollback_boundary_set": deepcopy(rollbacks),
            "preflight_artifact_digest": preflight["content_digest"],
            "preflight_id": preflight_data["preflight_id"],
            "readiness_artifact_digest": readiness["content_digest"],
            "readiness_assessment_id": readiness_data["assessment_id"],
            "completion_artifact_digest": completion["content_digest"],
            "final_completion_receipt_digest": data["final_completion_receipt_digest"],
            "canonical_chain_digest": data["canonical_chain_digest"],
        }

    def _new_state(self, input_identity: dict[str, str]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_PREFLIGHT_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": input_identity,
            "attempts": {"execution_preflight_evaluation": 0, "artifact_assembly": 0},
            "evaluation": None,
            "metrics": {
                "execution_preflight_validation_checks": 0,
                "execution_preflight_evaluation_attempts": 0,
                "execution_preflight_evaluation_reuse": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "blocked_classifications": 0,
                "execution_review_ready_classifications": 0,
                "invalid_classifications": 0,
                "recovery_attempts": 0,
                "elapsed_ms": 0,
                "anti_rework": {
                    "locked_iterations_1_13_reexecution": 0,
                    "iteration13_admission_evaluation_reexecution": 0,
                    "iteration13_admission_artifact_rebuild": 0,
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
                raise IntegrationExecutionPreflightError(
                    "execution-preflight state identity is required"
                )
            return self._new_state(input_identity)
        if (
            state.get("schema_version") != EXECUTION_PREFLIGHT_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationExecutionPreflightError(
                "Iteration 14 execution-preflight state is stale or schema-incompatible"
            )
        if input_identity is not None and state.get("input_identity") != input_identity:
            raise IntegrationExecutionPreflightError(
                "cached execution-preflight state binds different admission/policy/manifest identities"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_PREFLIGHT_SCHEMA_VERSION,
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
                "schema_version": EXECUTION_PREFLIGHT_SCHEMA_VERSION,
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
            raise IntegrationExecutionPreflightError(
                "execution-preflight recovery incident binds different input identity"
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

    def _explicit_references(self, record: dict[str, Any]) -> dict[str, Any]:
        return {
            key: deepcopy(record[key])
            for key in self.EXPLICIT_REFERENCE_FIELDS
            if key in record
        }

    def _validate_present_evidence(
        self, key: str, record: dict[str, Any], context: dict[str, Any]
    ) -> str | None:
        if not record.get("record_id"):
            raise IntegrationExecutionPreflightError(
                f"{key} execution-envelope evidence has no record_id"
            )
        if record.get("record_kind") != self.EXPECTED_RECORD_KINDS[key]:
            raise IntegrationExecutionPreflightError(
                f"{key} execution-envelope evidence record_kind is unsupported"
            )
        if record.get("synthetic_only") is not True:
            raise IntegrationExecutionPreflightError(
                f"{key} execution-envelope evidence must remain synthetic_only"
            )
        if record.get("production_action_authorized") is not False:
            raise IntegrationExecutionPreflightError(
                f"{key} execution-envelope evidence cannot authorize production action"
            )

        if key == "executor_contract":
            if not record.get("executor_contract_id") or not record.get("executor_contract_version"):
                raise IntegrationExecutionPreflightError(
                    "executor contract identity/version is incomplete"
                )
        elif key == "step_selection_scope":
            if (
                record.get("plan_id") != context["plan_id"]
                or record.get("plan_graph_digest") != context["plan_graph_digest"]
                or record.get("step_ids")
                != [item["step_id"] for item in context["plan_steps"]]
            ):
                raise IntegrationExecutionPreflightError(
                    "execution step-selection scope does not exactly bind the locked ten-step plan graph"
                )
        elif key == "step_enablement":
            if record.get("plan_id") != context["plan_id"]:
                raise IntegrationExecutionPreflightError(
                    "execution step-enablement plan identity changed"
                )
            steps = record.get("steps")
            expected_ids = [item["step_id"] for item in context["plan_steps"]]
            if (
                not isinstance(steps, list)
                or [item.get("step_id") for item in steps if isinstance(item, dict)]
                != expected_ids
            ):
                raise IntegrationExecutionPreflightError(
                    "execution step-enablement inventory is incomplete or ambiguous"
                )
            if any(
                item.get("enabled") is not False
                or item.get("production_action_authorized") is not False
                for item in steps
            ):
                return "EXECUTION_REAL_STEP_ENABLED"
        elif key == "dry_run_assertions":
            if (
                record.get("dry_run_assertion_set_digest")
                != context["dry_run_assertion_set_digest"]
            ):
                raise IntegrationExecutionPreflightError(
                    "execution dry-run assertion binding changed"
                )
        elif key == "rollback_restore":
            if (
                record.get("rollback_boundary_set_digest")
                != context["rollback_boundary_set_digest"]
                or not record.get("restore_point_id")
            ):
                raise IntegrationExecutionPreflightError(
                    "execution rollback/restore binding is incomplete or changed"
                )
            if record.get("rollback_execution_authorized") is not False:
                return "EXECUTION_ROLLBACK_ACTION_AUTHORIZED"
        elif key == "target_environment":
            if (
                not record.get("target_environment_id")
                or record.get("environment_class") != "synthetic_nonproduction"
                or record.get("production_target") is not False
            ):
                return "EXECUTION_TARGET_ENVIRONMENT_NOT_SYNTHETIC_NONPRODUCTION"
        elif key == "pre_execution_verification":
            if (
                not record.get("verification_policy_id")
                or record.get("required") is not True
                or record.get("approved_for_execution") is not False
            ):
                return "EXECUTION_PRE_EXECUTION_VERIFICATION_UNSAFE"
        elif key == "stop_abort_conditions":
            conditions = record.get("stop_conditions")
            if (
                not record.get("policy_id")
                or not isinstance(conditions, list)
                or not conditions
                or record.get("abort_on_identity_mismatch") is not True
                or record.get("abort_on_cost_guard_failure") is not True
            ):
                return "EXECUTION_STOP_ABORT_CONDITIONS_INCOMPLETE"
        elif key == "cutover_decommission_state":
            if (
                record.get("cutover_authorized") is not False
                or record.get("legacy_decommission_authorized") is not False
                or record.get("readers_routed_to_greenfield") is not False
            ):
                return "EXECUTION_CUTOVER_OR_DECOMMISSION_AUTHORIZED"
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
                raise IntegrationExecutionPreflightError(
                    "execution zero-cost evidence is ambiguous"
                )
            if (
                record.get("approved") is not True
                or record.get("zero_incremental_cost") is not True
                or any(
                    record.get(field) is not False
                    for field in (
                        "separately_billed_openai_api_required",
                        "paid_completion_or_storage_api_required",
                        "paid_deployment_or_hosting_api_required",
                        "other_incremental_paid_dependency_required",
                    )
                )
            ):
                return "EXECUTION_ZERO_INCREMENTAL_COST_GUARD_FAILED"
        return None

    def _decision_binding(
        self, decision: dict[str, Any] | None, manifest_id: str
    ) -> tuple[dict[str, Any], str | None]:
        if decision is None:
            return {
                "record_id": None,
                "decision_id": None,
                "record_digest": None,
                "decision": None,
            }, "EXECUTION_ENVELOPE_DECISION_MISSING"
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
            "admission_binding_mode",
            "execution_envelope_manifest_id",
            "every_real_step_disabled",
        )
        missing = [key for key in required if key not in decision]
        if missing:
            raise IntegrationExecutionPreflightError(
                f"execution-envelope decision is ambiguous: missing {','.join(missing)}"
            )
        if decision.get("record_kind") != "production-integration-execution-envelope-decision":
            raise IntegrationExecutionPreflightError(
                "execution-envelope decision record_kind is unsupported"
            )
        if decision.get("synthetic_only") is not True:
            raise IntegrationExecutionPreflightError(
                "execution-envelope decision must remain synthetic_only"
            )
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if decision.get(flag) is not False:
                raise IntegrationExecutionPreflightError(
                    f"execution-envelope decision cannot authorize {flag}"
                )
        if (
            decision.get("approved") is not True
            or decision.get("decision")
            != "execution_review_ready_for_later_separately_authorized_executor"
            or decision.get("scope") != "execution_preflight_only"
            or decision.get("admission_binding_mode")
            != "exact_locked_admission_artifact"
            or decision.get("execution_envelope_manifest_id") != manifest_id
            or decision.get("every_real_step_disabled") is not True
        ):
            return {
                "record_id": decision.get("record_id"),
                "decision_id": decision.get("decision_id"),
                "record_digest": digest(decision),
                "decision": decision.get("decision"),
            }, "EXECUTION_ENVELOPE_DECISION_NOT_APPROVED"
        return {
            "record_id": decision["record_id"],
            "decision_id": decision["decision_id"],
            "record_digest": digest(decision),
            "decision": decision["decision"],
        }, None

    def _evaluate(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
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
            reason = self._validate_present_evidence(key, record, context)
            bindings[key] = {
                "evidence_source": "repository_execution_envelope_manifest",
                "record_id": record["record_id"],
                "record_digest": digest(record),
                "explicit_references": self._explicit_references(record),
            }
            if reason:
                missing_or_blocking.append(reason)

        decision_binding, decision_reason = self._decision_binding(
            manifest.get("execution_envelope_decision"), manifest["manifest_id"]
        )
        if decision_reason:
            missing_or_blocking.append(decision_reason)

        if context["admission_classification"] == "invalid":
            classification = "invalid"
            reason_codes = [
                "ITERATION13_ADMISSION_INVALID",
                *context["admission_reason_codes"],
            ]
        elif context["admission_classification"] == "blocked":
            classification = "blocked"
            reason_codes = [
                "ITERATION13_ADMISSION_BLOCKED",
                *context["admission_reason_codes"],
            ]
        elif context["admission_classification"] == "authorization_ready":
            if missing_or_blocking:
                classification = "blocked"
                reason_codes = missing_or_blocking
            else:
                classification = "execution_review_ready"
                reason_codes = [policy["execution_review_ready_reason_code"]]
        else:
            raise IntegrationExecutionPreflightError(
                "unsupported Iteration 13 admission classification"
            )

        if classification == "execution_review_ready":
            if context["admission_classification"] != "authorization_ready":
                raise IntegrationExecutionPreflightError(
                    "blocked/invalid admission cannot silently become execution_review_ready"
                )
            if decision_binding["decision_id"] is None:
                raise IntegrationExecutionPreflightError(
                    "execution_review_ready requires a separate execution-envelope decision"
                )
            step_binding = bindings["step_enablement"]["explicit_references"].get("steps") or []
            if any(item.get("enabled") is not False for item in step_binding):
                raise IntegrationExecutionPreflightError(
                    "execution_review_ready cannot enable any real integration step"
                )

        return {
            "classification": classification,
            "classification_reason_codes": reason_codes,
            "execution_envelope_bindings": bindings,
            "execution_envelope_decision_binding": decision_binding,
        }

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        context = self._admission_context(run)
        policy, manifest = self._policy_and_manifest()
        input_identity = {
            "admission_artifact_digest": context["admission_artifact_digest"],
            "admission_id": context["admission_id"],
            "execution_preflight_policy_digest": digest(policy),
            "execution_envelope_manifest_digest": digest(manifest),
        }
        state = self._load_state(input_identity)
        state["metrics"]["execution_preflight_validation_checks"] += 1
        if state.get("evaluation") is not None:
            state["metrics"]["execution_preflight_evaluation_reuse"] += 1
            state["metrics"]["elapsed_ms"] = max(
                0, int((time.monotonic() - started) * 1000)
            )
            self._save_state(state)
            self._write_metrics(state)
            return deepcopy(state["evaluation"])

        state["attempts"]["execution_preflight_evaluation"] += 1
        state["metrics"]["execution_preflight_evaluation_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "evaluation" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("evaluation", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationExecutionPreflightBoundaryFailure(
                "integration_execution_preflight_evaluation",
                "evaluation",
                self.failure_class,
            )

        evaluated = self._evaluate(context, policy, manifest)
        state["evaluation"] = {
            **evaluated,
            "input_identity": input_identity,
            "execution_preflight_policy_version": policy[
                "execution_preflight_policy_version"
            ],
            "execution_preflight_policy_id": policy["policy_id"],
            "execution_envelope_manifest_id": manifest["manifest_id"],
            **deepcopy(context),
        }
        state["metrics"]["elapsed_ms"] = max(
            0, int((time.monotonic() - started) * 1000)
        )
        self._save_state(state)
        self._write_metrics(state)
        return deepcopy(state["evaluation"])

    def _artifact_data(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        identity = evaluated["input_identity"]
        decision = evaluated["execution_envelope_decision_binding"]
        semantic_identity = {
            "execution_preflight_schema_version": EXECUTION_PREFLIGHT_SCHEMA_VERSION,
            "execution_preflight_policy_version": evaluated[
                "execution_preflight_policy_version"
            ],
            "execution_preflight_policy_id": evaluated[
                "execution_preflight_policy_id"
            ],
            "execution_preflight_policy_digest": identity[
                "execution_preflight_policy_digest"
            ],
            "execution_envelope_manifest_id": evaluated[
                "execution_envelope_manifest_id"
            ],
            "execution_envelope_manifest_digest": identity[
                "execution_envelope_manifest_digest"
            ],
            "admission_artifact_digest": evaluated["admission_artifact_digest"],
            "admission_id": evaluated["admission_id"],
            "admission_schema_version": evaluated["admission_schema_version"],
            "admission_policy_version": evaluated["admission_policy_version"],
            "admission_classification": evaluated["admission_classification"],
            "admission_reason_codes": evaluated["admission_reason_codes"],
            "admission_evidence_binding_digest": evaluated[
                "admission_evidence_binding_digest"
            ],
            "admission_decision_id": evaluated["admission_decision_id"],
            "admission_decision_digest": evaluated["admission_decision_digest"],
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
            "execution_envelope_bindings": evaluated[
                "execution_envelope_bindings"
            ],
            "execution_envelope_decision_id": decision["decision_id"],
            "execution_envelope_decision_digest": decision["record_digest"],
        }
        step_refs = evaluated["execution_envelope_bindings"]["step_enablement"][
            "explicit_references"
        ]
        return {
            **semantic_identity,
            "execution_preflight_id": digest(semantic_identity),
            "execution_steps": deepcopy(step_refs.get("steps") or []),
            "real_integration_steps_enabled": sum(
                1 for item in (step_refs.get("steps") or []) if item.get("enabled") is True
            ),
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_execution_preflight_only",
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
            raise IntegrationExecutionPreflightBoundaryFailure(
                "execution_preflight_validation",
                "execution_preflight_artifact",
                "cached execution-preflight artifact is not locked",
            )
        if semantic_digest(existing) != existing.get("content_digest"):
            raise IntegrationExecutionPreflightBoundaryFailure(
                "execution_preflight_validation",
                "execution_preflight_artifact",
                "cached execution-preflight artifact is corrupted",
            )
        if existing.get("data") != self._artifact_data(run, evaluated):
            raise IntegrationExecutionPreflightBoundaryFailure(
                "execution_preflight_validation",
                "execution_preflight_artifact",
                "cached execution-preflight artifact binds different admission/policy/manifest identities",
            )
        state = self._load_state(evaluated["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_preflight(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id == "final_execution_preflight_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._record_incident(
                "final_execution_preflight_artifact", self.failure_class, state
            )
            self._write_metrics(state)
            raise IntegrationExecutionPreflightBoundaryFailure(
                "integration_execution_preflight_artifact_assembly",
                "final_execution_preflight_artifact",
                self.failure_class,
            )
        return self._artifact_data(run, evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionPreflightError(
                "final production integration execution-preflight artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionPreflightError(
                "final production integration execution-preflight artifact digest is invalid"
            )
        data = artifact.get("data") or {}
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
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
                raise IntegrationExecutionPreflightError(
                    f"integration execution preflight cannot authorize/mutate {flag}"
                )
        if data.get("real_integration_steps_enabled") != 0:
            raise IntegrationExecutionPreflightError(
                "Iteration 14 cannot enable any real integration step"
            )
        if any(item.get("enabled") is not False for item in data.get("execution_steps") or []):
            raise IntegrationExecutionPreflightError(
                "Iteration 14 execution steps must remain disabled"
            )
        if data.get("classification") == "execution_review_ready":
            if data.get("admission_classification") != "authorization_ready":
                raise IntegrationExecutionPreflightError(
                    "blocked/invalid admission cannot silently become execution_review_ready"
                )
            if not data.get("execution_envelope_decision_id"):
                raise IntegrationExecutionPreflightError(
                    "execution_review_ready requires an explicit execution-envelope decision"
                )
        state = self._load_state()
        classification = data.get("classification")
        if classification == "blocked":
            state["metrics"]["blocked_classifications"] += 1
        elif classification == "execution_review_ready":
            state["metrics"]["execution_review_ready_classifications"] += 1
        elif classification == "invalid":
            state["metrics"]["invalid_classifications"] += 1
        else:
            raise IntegrationExecutionPreflightError(
                "unsupported integration execution-preflight classification"
            )
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
