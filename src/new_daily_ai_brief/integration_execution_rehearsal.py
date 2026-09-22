from __future__ import annotations

import json
import re
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    ADMISSION_POLICY_VERSION,
    ADMISSION_SCHEMA_VERSION,
    EXECUTION_PREFLIGHT_POLICY_VERSION,
    EXECUTION_PREFLIGHT_SCHEMA_VERSION,
    EXECUTION_REHEARSAL_POLICY_VERSION,
    EXECUTION_REHEARSAL_SCHEMA_VERSION,
    PLAN_POLICY_VERSION,
    PLAN_SCHEMA_VERSION,
    PREFLIGHT_POLICY_VERSION,
    PREFLIGHT_SCHEMA_VERSION,
    READINESS_POLICY_VERSION,
    READINESS_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class IntegrationExecutionRehearsalError(ContractError):
    pass


class IntegrationExecutionRehearsalBoundaryFailure(IntegrationExecutionRehearsalError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"execution_rehearsal:{boundary_id}"


class ProductionIntegrationExecutionRehearsal:
    """Deterministic, synthetic-only Iteration 15 no-op execution rehearsal."""

    REQUIRED_EVIDENCE = (
        "runner_contract",
        "step_selection_scope",
        "noop_policy",
        "dry_run_assertions",
        "rollback_restore",
        "target_environment",
        "pre_rehearsal_verification",
        "stop_abort_conditions",
        "cutover_decommission_state",
        "zero_incremental_cost",
    )

    MISSING_REASON_CODES = {
        "runner_contract": "REHEARSAL_RUNNER_CONTRACT_MISSING",
        "step_selection_scope": "REHEARSAL_STEP_SELECTION_SCOPE_MISSING",
        "noop_policy": "REHEARSAL_NOOP_POLICY_MISSING",
        "dry_run_assertions": "REHEARSAL_DRY_RUN_BINDING_MISSING",
        "rollback_restore": "REHEARSAL_ROLLBACK_RESTORE_BINDING_MISSING",
        "target_environment": "REHEARSAL_TARGET_ENVIRONMENT_MISSING",
        "pre_rehearsal_verification": "REHEARSAL_PRE_VERIFICATION_MISSING",
        "stop_abort_conditions": "REHEARSAL_STOP_ABORT_CONDITIONS_MISSING",
        "cutover_decommission_state": "REHEARSAL_CUTOVER_DECOMMISSION_STATE_MISSING",
        "zero_incremental_cost": "REHEARSAL_ZERO_INCREMENTAL_COST_GUARD_MISSING",
    }

    EXPECTED_RECORD_KINDS = {
        "runner_contract": "production-integration-rehearsal-runner-contract",
        "step_selection_scope": "production-integration-rehearsal-step-selection-scope",
        "noop_policy": "production-integration-rehearsal-noop-policy",
        "dry_run_assertions": "production-integration-rehearsal-dry-run-binding",
        "rollback_restore": "production-integration-rehearsal-rollback-restore-binding",
        "target_environment": "production-integration-rehearsal-target-environment",
        "pre_rehearsal_verification": "production-integration-rehearsal-pre-verification-policy",
        "stop_abort_conditions": "production-integration-rehearsal-stop-abort-policy",
        "cutover_decommission_state": "production-integration-rehearsal-cutover-decommission-state",
        "zero_incremental_cost": "cost-policy-approval",
    }

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_integration_execution_rehearsal_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("execution_rehearsal:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration15-execution-rehearsal-state.json"
        self.metrics_path = self.store.run_dir / "iteration15-execution-rehearsal-metrics.json"
        self.incident_path = self.store.run_dir / "iteration15-execution-rehearsal-incident.json"
        self.final_receipt_path = self.store.run_dir / "iteration9-final-completion-receipt.json"

    def _read_json_fixture(self, name: str) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionRehearsalError(
                "production integration execution rehearsal is synthetic-only and fail-closed"
            )
        path = self.fixture_root / name
        if not path.exists():
            raise IntegrationExecutionRehearsalError(
                f"missing Iteration 15 execution-rehearsal fixture: {path}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _policy_and_manifest(self) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self._read_json_fixture("rehearsal-policy.json")
        manifest = self._read_json_fixture("rehearsal-envelope-manifest.json")
        if (
            policy.get("schema_version") != EXECUTION_REHEARSAL_SCHEMA_VERSION
            or policy.get("execution_rehearsal_policy_version") != EXECUTION_REHEARSAL_POLICY_VERSION
            or policy.get("policy_id") != "production-integration-execution-rehearsal-v1"
        ):
            raise IntegrationExecutionRehearsalError(
                "unsupported Iteration 15 execution-rehearsal policy/schema identity"
            )
        if policy.get("synthetic_only") is not True:
            raise IntegrationExecutionRehearsalError("rehearsal policy must remain synthetic_only")
        if policy.get("production_action_authorized") is not False:
            raise IntegrationExecutionRehearsalError("rehearsal policy cannot authorize production")
        if policy.get("require_exact_execution_preflight_binding") is not True:
            raise IntegrationExecutionRehearsalError("exact Iteration 14 binding is required")
        if policy.get("require_separate_rehearsal_decision") is not True:
            raise IntegrationExecutionRehearsalError("separate rehearsal decision is required")
        if policy.get("require_exactly_ten_noop_receipts") is not True:
            raise IntegrationExecutionRehearsalError("exactly ten no-op receipts are required")
        if tuple(policy.get("required_evidence") or ()) != self.REQUIRED_EVIDENCE:
            raise IntegrationExecutionRehearsalError("rehearsal evidence inventory is incomplete")
        if policy.get("classifications") != ["blocked", "rehearsal_complete", "invalid"]:
            raise IntegrationExecutionRehearsalError("unsupported rehearsal classifications")

        if (
            manifest.get("schema_version") != EXECUTION_REHEARSAL_SCHEMA_VERSION
            or manifest.get("rehearsal_envelope_manifest_version") != "1.0.0"
            or not manifest.get("manifest_id")
        ):
            raise IntegrationExecutionRehearsalError("unsupported rehearsal manifest identity")
        if manifest.get("synthetic_only") is not True:
            raise IntegrationExecutionRehearsalError("rehearsal manifest must remain synthetic_only")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if manifest.get(flag) is not False:
                raise IntegrationExecutionRehearsalError(
                    f"rehearsal manifest cannot authorize {flag}"
                )
        closure = manifest.get("iteration14_closure") or {}
        if (
            closure.get("repository_closure_status") != "complete"
            or closure.get("iteration15_ready") is not True
            or closure.get("evidence_path")
            != "evidence/iteration14/synthetic-shadow-production-integration-execution-preflight-evidence.json"
        ):
            raise IntegrationExecutionRehearsalError("Iteration 14 closure is incomplete or untrusted")
        binding = manifest.get("execution_preflight_binding") or {}
        if binding != {
            "binding_type": "exact_locked_execution_preflight_artifact",
            "artifact_type": "production-integration-execution-preflight",
            "execution_preflight_id_field": "data.execution_preflight_id",
            "artifact_digest_field": "content_digest",
        }:
            raise IntegrationExecutionRehearsalError("rehearsal preflight binding declaration is invalid")
        evidence = manifest.get("evidence")
        if not isinstance(evidence, dict) or tuple(evidence.keys()) != self.REQUIRED_EVIDENCE:
            raise IntegrationExecutionRehearsalError("rehearsal evidence map is incomplete or ambiguous")
        decision = manifest.get("rehearsal_decision")
        if decision is not None and not isinstance(decision, dict):
            raise IntegrationExecutionRehearsalError("rehearsal decision must be explicit record or null")
        return policy, manifest

    def _execution_preflight_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        keys = (
            "execution_preflight_schema_version",
            "execution_preflight_policy_version",
            "execution_preflight_policy_id",
            "execution_preflight_policy_digest",
            "execution_envelope_manifest_id",
            "execution_envelope_manifest_digest",
            "admission_artifact_digest",
            "admission_id",
            "admission_schema_version",
            "admission_policy_version",
            "admission_classification",
            "admission_reason_codes",
            "admission_evidence_binding_digest",
            "admission_decision_id",
            "admission_decision_digest",
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
            "execution_envelope_bindings",
            "execution_envelope_decision_id",
            "execution_envelope_decision_digest",
        )
        return {key: deepcopy(data.get(key)) for key in keys}

    def _preflight_context(self, run: dict[str, Any]) -> dict[str, Any]:
        if run.get("current_state") != "Complete" or run.get("completion_status") != "complete_locked":
            raise IntegrationExecutionRehearsalError(
                "integration_execution_rehearsal_only requires Complete / complete_locked"
            )
        execution_preflight = self.store.load_artifact(
            "production-integration-execution-preflight"
        )
        if not execution_preflight or execution_preflight.get("status") != "locked":
            raise IntegrationExecutionRehearsalError("locked Iteration 14 execution preflight is missing")
        if semantic_digest(execution_preflight) != execution_preflight.get("content_digest"):
            raise IntegrationExecutionRehearsalError("locked Iteration 14 execution preflight is corrupted")
        data = execution_preflight.get("data") or {}
        if (
            data.get("execution_preflight_schema_version") != EXECUTION_PREFLIGHT_SCHEMA_VERSION
            or data.get("execution_preflight_policy_version") != EXECUTION_PREFLIGHT_POLICY_VERSION
        ):
            raise IntegrationExecutionRehearsalError("Iteration 14 execution preflight version unsupported")
        if digest(self._execution_preflight_identity(data)) != data.get("execution_preflight_id"):
            raise IntegrationExecutionRehearsalError("Iteration 14 execution preflight identity is corrupted")
        if (
            data.get("final_state") != "Complete"
            or data.get("final_status") != "complete_locked"
            or data.get("completion_scope") != "synthetic_shadow_execution_preflight_only"
            or data.get("synthetic_only") is not True
            or data.get("real_integration_steps_enabled") != 0
        ):
            raise IntegrationExecutionRehearsalError("Iteration 14 execution preflight semantics are stale")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if data.get(flag) is not False:
                raise IntegrationExecutionRehearsalError(
                    f"Iteration 14 execution preflight cannot authorize {flag}"
                )
        if any(item.get("enabled") is not False for item in data.get("execution_steps") or []):
            raise IntegrationExecutionRehearsalError("Iteration 14 real integration steps must be disabled")

        admission = self.store.load_artifact("production-integration-admission")
        plan = self.store.load_artifact("production-integration-plan")
        preflight = self.store.load_artifact("production-integration-preflight")
        readiness = self.store.load_artifact("readiness-admission")
        completion = self.store.load_artifact("completion")
        for name, artifact in (
            ("production-integration-admission", admission),
            ("production-integration-plan", plan),
            ("production-integration-preflight", preflight),
            ("readiness-admission", readiness),
            ("completion", completion),
        ):
            if not artifact or artifact.get("status") != "locked":
                raise IntegrationExecutionRehearsalError(f"bound upstream artifact {name} is missing")
            if semantic_digest(artifact) != artifact.get("content_digest"):
                raise IntegrationExecutionRehearsalError(f"bound upstream artifact {name} is corrupted")

        ad = admission["data"]
        pd = plan["data"]
        pfd = preflight["data"]
        rd = readiness["data"]
        cd = completion["data"]
        if (
            ad.get("admission_schema_version") != ADMISSION_SCHEMA_VERSION
            or ad.get("admission_policy_version") != ADMISSION_POLICY_VERSION
            or pd.get("plan_schema_version") != PLAN_SCHEMA_VERSION
            or pd.get("plan_policy_version") != PLAN_POLICY_VERSION
            or pfd.get("preflight_schema_version") != PREFLIGHT_SCHEMA_VERSION
            or pfd.get("preflight_policy_version") != PREFLIGHT_POLICY_VERSION
            or rd.get("readiness_schema_version") != READINESS_SCHEMA_VERSION
            or rd.get("readiness_policy_version") != READINESS_POLICY_VERSION
        ):
            raise IntegrationExecutionRehearsalError("bound upstream schema/policy version unsupported")

        dependency_checks = (
            execution_preflight.get("input_digests") == [admission["content_digest"]],
            admission.get("input_digests") == [plan["content_digest"]],
            plan.get("input_digests") == [preflight["content_digest"]],
            preflight.get("input_digests") == [readiness["content_digest"]],
            readiness.get("input_digests") == [completion["content_digest"]],
        )
        if not all(dependency_checks):
            raise IntegrationExecutionRehearsalError("transitive upstream dependency identity changed")

        exact = (
            data.get("admission_artifact_digest") == admission["content_digest"],
            data.get("admission_id") == ad.get("admission_id"),
            data.get("plan_artifact_digest") == plan["content_digest"],
            data.get("plan_id") == pd.get("plan_id"),
            data.get("plan_graph_digest") == digest(pd.get("plan_steps") or []),
            data.get("dry_run_assertion_set_digest") == digest(pd.get("dry_run_assertion_set") or []),
            data.get("rollback_boundary_set_digest") == digest(pd.get("rollback_boundary_set") or []),
            data.get("preflight_artifact_digest") == preflight["content_digest"],
            data.get("preflight_id") == pfd.get("preflight_id"),
            data.get("readiness_artifact_digest") == readiness["content_digest"],
            data.get("readiness_assessment_id") == rd.get("assessment_id"),
            data.get("completion_artifact_digest") == completion["content_digest"],
            data.get("canonical_chain_digest") == cd.get("canonical_chain_digest"),
        )
        if not all(exact):
            raise IntegrationExecutionRehearsalError("Iteration 14 bound upstream identity changed")
        final_receipt = self.store.read_json(self.final_receipt_path)
        if not final_receipt or digest(final_receipt) != data.get("final_completion_receipt_digest"):
            raise IntegrationExecutionRehearsalError("Iteration 9 final completion receipt identity changed")

        steps = pd.get("plan_steps") or []
        assertions = pd.get("dry_run_assertion_set") or []
        rollbacks = pd.get("rollback_boundary_set") or []
        if len(steps) != 10 or len({x.get("step_id") for x in steps}) != 10:
            raise IntegrationExecutionRehearsalError("locked ten-step plan graph is incomplete")
        classification = data.get("classification")
        if classification not in {"blocked", "execution_review_ready", "invalid"}:
            raise IntegrationExecutionRehearsalError("unsupported Iteration 14 preflight classification")
        return {
            "execution_preflight_artifact_digest": execution_preflight["content_digest"],
            "execution_preflight_id": data["execution_preflight_id"],
            "execution_preflight_classification": classification,
            "execution_preflight_reason_codes": deepcopy(data.get("classification_reason_codes") or []),
            "execution_preflight_policy_id": data.get("execution_preflight_policy_id"),
            "execution_preflight_policy_digest": data.get("execution_preflight_policy_digest"),
            "execution_envelope_manifest_id": data.get("execution_envelope_manifest_id"),
            "execution_envelope_manifest_digest": data.get("execution_envelope_manifest_digest"),
            "execution_envelope_decision_id": data.get("execution_envelope_decision_id"),
            "execution_envelope_decision_digest": data.get("execution_envelope_decision_digest"),
            "execution_steps": deepcopy(data.get("execution_steps") or []),
            "admission_artifact_digest": admission["content_digest"],
            "admission_id": ad["admission_id"],
            "plan_artifact_digest": plan["content_digest"],
            "plan_id": pd["plan_id"],
            "plan_graph_digest": digest(steps),
            "dry_run_assertion_set_digest": digest(assertions),
            "rollback_boundary_set_digest": digest(rollbacks),
            "plan_steps": deepcopy(steps),
            "dry_run_assertion_set": deepcopy(assertions),
            "rollback_boundary_set": deepcopy(rollbacks),
            "preflight_artifact_digest": preflight["content_digest"],
            "preflight_id": pfd["preflight_id"],
            "readiness_artifact_digest": readiness["content_digest"],
            "readiness_assessment_id": rd["assessment_id"],
            "completion_artifact_digest": completion["content_digest"],
            "final_completion_receipt_digest": data["final_completion_receipt_digest"],
            "canonical_chain_digest": data["canonical_chain_digest"],
        }

    def _decision_binding(self, decision: dict[str, Any] | None, manifest_id: str) -> tuple[dict[str, Any], str | None]:
        if decision is None:
            return {"decision_id": None, "record_digest": None, "decision": None}, "REHEARSAL_DECISION_MISSING"
        required = (
            "record_id", "record_kind", "decision_id", "decision", "approved",
            "synthetic_only", "production_action_authorized", "production_cutover_authorized",
            "legacy_decommission_authorized", "production_publication", "scope",
            "execution_preflight_binding_mode", "rehearsal_envelope_manifest_id",
            "every_real_step_disabled",
        )
        missing = [key for key in required if key not in decision]
        if missing:
            raise IntegrationExecutionRehearsalError(
                "rehearsal decision is ambiguous: missing " + ",".join(missing)
            )
        if decision.get("record_kind") != "production-integration-execution-rehearsal-decision":
            raise IntegrationExecutionRehearsalError("rehearsal decision record_kind unsupported")
        if decision.get("synthetic_only") is not True:
            raise IntegrationExecutionRehearsalError("rehearsal decision must remain synthetic_only")
        for flag in (
            "production_action_authorized", "production_cutover_authorized",
            "legacy_decommission_authorized", "production_publication",
        ):
            if decision.get(flag) is not False:
                raise IntegrationExecutionRehearsalError(f"rehearsal decision cannot authorize {flag}")
        binding = {
            "decision_id": decision.get("decision_id"),
            "record_digest": digest(decision),
            "decision": decision.get("decision"),
        }
        if (
            decision.get("approved") is not True
            or decision.get("decision") != "authorize_synthetic_noop_rehearsal"
            or decision.get("scope") != "execution_rehearsal_only"
            or decision.get("execution_preflight_binding_mode")
            != "exact_locked_execution_preflight_artifact"
            or decision.get("rehearsal_envelope_manifest_id") != manifest_id
            or decision.get("every_real_step_disabled") is not True
        ):
            return binding, "REHEARSAL_DECISION_NOT_APPROVED"
        return binding, None

    def _validate_evidence(self, key: str, record: dict[str, Any], context: dict[str, Any]) -> str | None:
        if not record.get("record_id") or record.get("record_kind") != self.EXPECTED_RECORD_KINDS[key]:
            raise IntegrationExecutionRehearsalError(f"{key} rehearsal evidence identity unsupported")
        if record.get("synthetic_only") is not True or record.get("production_action_authorized") is not False:
            raise IntegrationExecutionRehearsalError(f"{key} rehearsal evidence is not synthetic-only")
        if key == "runner_contract":
            if (
                record.get("runner_contract_id") != "synthetic-noop-rehearsal-runner"
                or record.get("runner_contract_version") != "1.0.0"
                or record.get("external_execution_supported") is not False
            ):
                return "REHEARSAL_RUNNER_CONTRACT_UNSAFE"
        elif key == "step_selection_scope":
            if (
                record.get("plan_id") != context["plan_id"]
                or record.get("plan_graph_digest") != context["plan_graph_digest"]
                or record.get("step_ids") != [x["step_id"] for x in context["plan_steps"]]
            ):
                raise IntegrationExecutionRehearsalError("rehearsal step scope changed")
        elif key == "noop_policy":
            steps = record.get("steps")
            expected_ids = [x["step_id"] for x in context["plan_steps"]]
            if not isinstance(steps, list) or [x.get("step_id") for x in steps] != expected_ids:
                raise IntegrationExecutionRehearsalError("rehearsal no-op step inventory incomplete")
            if any(
                x.get("noop") is not True
                or x.get("real_executable") is not False
                or x.get("external_execution_performed") is not False
                or x.get("production_action_authorized") is not False
                for x in steps
            ):
                raise IntegrationExecutionRehearsalError(
                    "real executable rehearsal step fails closed before final artifact lock"
                )
        elif key == "dry_run_assertions":
            if record.get("dry_run_assertion_set_digest") != context["dry_run_assertion_set_digest"]:
                raise IntegrationExecutionRehearsalError("rehearsal dry-run assertion binding changed")
        elif key == "rollback_restore":
            if (
                record.get("rollback_boundary_set_digest") != context["rollback_boundary_set_digest"]
                or not record.get("restore_point_id")
                or record.get("rollback_execution_authorized") is not False
            ):
                return "REHEARSAL_ROLLBACK_RESTORE_UNSAFE"
        elif key == "target_environment":
            if (
                record.get("target_environment_id") != "synthetic-shadow-rehearsal"
                or record.get("environment_class") != "synthetic_nonproduction"
                or record.get("production_target") is not False
            ):
                return "REHEARSAL_TARGET_ENVIRONMENT_NOT_SYNTHETIC"
        elif key == "pre_rehearsal_verification":
            if (
                not record.get("verification_policy_id")
                or record.get("required") is not True
                or record.get("approved_for_real_execution") is not False
            ):
                return "REHEARSAL_PRE_VERIFICATION_UNSAFE"
        elif key == "stop_abort_conditions":
            if (
                not record.get("policy_id")
                or not record.get("stop_conditions")
                or record.get("abort_on_identity_mismatch") is not True
                or record.get("abort_on_unexpected_executable_step") is not True
                or record.get("abort_on_cost_guard_failure") is not True
            ):
                return "REHEARSAL_STOP_ABORT_CONDITIONS_INCOMPLETE"
        elif key == "cutover_decommission_state":
            if (
                record.get("cutover_authorized") is not False
                or record.get("legacy_decommission_authorized") is not False
                or record.get("readers_routed_to_greenfield") is not False
            ):
                return "REHEARSAL_CUTOVER_OR_DECOMMISSION_AUTHORIZED"
        elif key == "zero_incremental_cost":
            required = (
                "approved", "zero_incremental_cost", "separately_billed_openai_api_required",
                "paid_completion_or_storage_api_required", "paid_deployment_or_hosting_api_required",
                "other_incremental_paid_dependency_required",
            )
            if any(field not in record for field in required):
                raise IntegrationExecutionRehearsalError("rehearsal zero-cost evidence ambiguous")
            if (
                record.get("approved") is not True
                or record.get("zero_incremental_cost") is not True
                or any(record.get(field) is not False for field in required[2:])
            ):
                return "REHEARSAL_ZERO_INCREMENTAL_COST_GUARD_FAILED"
        return None

    def _evaluate(
        self, context: dict[str, Any], policy: dict[str, Any], manifest: dict[str, Any]
    ) -> dict[str, Any]:
        bindings: dict[str, Any] = {}
        blocking: list[str] = []
        if context["execution_preflight_classification"] == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION14_EXECUTION_PREFLIGHT_INVALID",
                    *context["execution_preflight_reason_codes"],
                ],
                "rehearsal_evidence_bindings": bindings,
                "rehearsal_decision_binding": {
                    "decision_id": None, "record_digest": None, "decision": None
                },
            }
        if context["execution_preflight_classification"] == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION14_EXECUTION_PREFLIGHT_BLOCKED",
                    *context["execution_preflight_reason_codes"],
                ],
                "rehearsal_evidence_bindings": bindings,
                "rehearsal_decision_binding": {
                    "decision_id": None, "record_digest": None, "decision": None
                },
            }
        if context["execution_preflight_classification"] != "execution_review_ready":
            raise IntegrationExecutionRehearsalError("unsupported Iteration 14 execution preflight classification")

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
            manifest.get("rehearsal_decision"), manifest["manifest_id"]
        )
        if decision_reason:
            blocking.append(decision_reason)
        if blocking:
            classification = "blocked"
            reasons = blocking
        else:
            classification = "rehearsal_complete"
            reasons = [policy["rehearsal_complete_reason_code"]]
        return {
            "classification": classification,
            "classification_reason_codes": reasons,
            "rehearsal_evidence_bindings": bindings,
            "rehearsal_decision_binding": decision_binding,
        }

    def _new_state(self, input_identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_REHEARSAL_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": input_identity,
            "attempts": {"evaluation": 0, "artifact_assembly": 0, "receipts": {}},
            "evaluation": None,
            "receipt_digests": {},
            "metrics": {
                "validation_checks": 0,
                "evaluation_attempts": 0,
                "evaluation_reuse": 0,
                "receipt_build_attempts": 0,
                "receipt_reuse": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "recovery_attempts": 0,
                "blocked_classifications": 0,
                "rehearsal_complete_classifications": 0,
                "invalid_classifications": 0,
                "elapsed_ms": 0,
                "anti_rework": {
                    "locked_iterations_1_14_reexecution": 0,
                    "iteration14_execution_preflight_reevaluation": 0,
                    "iteration14_execution_preflight_rebuild": 0,
                    "full_pipeline_restarts": 0,
                },
            },
        }

    def _load_state(self, input_identity: dict[str, Any] | None = None, *, optional: bool = False) -> dict[str, Any] | None:
        state = self.store.read_json(self.state_path)
        if state is None:
            if optional:
                return None
            if input_identity is None:
                raise IntegrationExecutionRehearsalError("rehearsal state input identity required")
            return self._new_state(input_identity)
        if (
            state.get("schema_version") != EXECUTION_REHEARSAL_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationExecutionRehearsalError("Iteration 15 rehearsal state is stale or incompatible")
        if input_identity is not None and state.get("input_identity") != input_identity:
            raise IntegrationExecutionRehearsalError(
                "cached rehearsal state binds different preflight/policy/manifest/decision identity"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_REHEARSAL_SCHEMA_VERSION,
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
                "schema_version": EXECUTION_REHEARSAL_SCHEMA_VERSION,
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
            raise IntegrationExecutionRehearsalError("rehearsal recovery incident identity changed")
        incident["result"] = "recovered"
        incident["recovery_receipt"] = {
            "boundary_id": incident["boundary_id"],
            "input_identity": deepcopy(state["input_identity"]),
            "result": "recovered",
            "recovered_at": utc_now(),
        }
        state["metrics"]["recovery_attempts"] += 1
        self.store._atomic_write(self.incident_path, incident)

    def _receipt_path(self, position: int, step_id: str) -> Path:
        safe = re.sub(r"[^a-z0-9-]+", "-", step_id.lower()).strip("-")
        return self.store.run_dir / f"iteration15-rehearsal-receipt-{position:02d}-{safe}.json"

    def _receipt_data(self, evaluated: dict[str, Any], position: int, step: dict[str, Any]) -> dict[str, Any]:
        step_id = step["step_id"]
        assertions = [
            x for x in evaluated["dry_run_assertion_set"] if x.get("step_id") == step_id
        ]
        rollbacks = [
            x for x in evaluated["rollback_boundary_set"] if x.get("step_id") == step_id
        ]
        body = {
            "schema_version": EXECUTION_REHEARSAL_SCHEMA_VERSION,
            "execution_attempt_id": evaluated["execution_attempt_id"],
            "position": position,
            "step_id": step_id,
            "plan_step_digest": digest(step),
            "assertion_binding_digest": digest(assertions),
            "rollback_binding_digest": digest(rollbacks),
            "dry_run_assertion_set_digest": evaluated["dry_run_assertion_set_digest"],
            "rollback_boundary_set_digest": evaluated["rollback_boundary_set_digest"],
            "execution_mode": "noop",
            "evaluation_result": "evaluated_not_executed",
            "external_execution_performed": False,
            "real_service_contacted": False,
            "side_effect_performed": False,
            "production_action_authorized": False,
            "synthetic_only": True,
        }
        return {**body, "receipt_id": digest(body)}

    def _ensure_receipts(self, evaluated: dict[str, Any], state: dict[str, Any]) -> list[dict[str, Any]]:
        if evaluated["classification"] != "rehearsal_complete":
            return []
        receipts: list[dict[str, Any]] = []
        for position, step in enumerate(evaluated["plan_steps"], 1):
            step_id = step["step_id"]
            path = self._receipt_path(position, step_id)
            expected = self._receipt_data(evaluated, position, step)
            existing = self.store.read_json(path)
            state["attempts"]["receipts"].setdefault(step_id, 0)
            if existing is not None:
                if existing != expected:
                    raise IntegrationExecutionRehearsalError(
                        f"cached rehearsal receipt identity changed for {step_id}"
                    )
                state["metrics"]["receipt_reuse"] += 1
                state["receipt_digests"][step_id] = digest(existing)
                receipts.append(existing)
                continue
            state["attempts"]["receipts"][step_id] += 1
            state["metrics"]["receipt_build_attempts"] += 1
            self._save_state(state)
            boundary = f"receipt:{step_id}"
            if self.failure_boundary_id == boundary and not self._failure_fired:
                self._failure_fired = True
                self._record_incident(boundary, self.failure_class, state)
                self._write_metrics(state)
                raise IntegrationExecutionRehearsalBoundaryFailure(
                    "integration_execution_rehearsal_receipt", boundary, self.failure_class
                )
            self.store._atomic_write(path, expected)
            state["receipt_digests"][step_id] = digest(expected)
            receipts.append(expected)
            self._save_state(state)
        if len(receipts) != 10:
            raise IntegrationExecutionRehearsalError("complete rehearsal must produce exactly ten receipts")
        return receipts

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        context = self._preflight_context(run)
        policy, manifest = self._policy_and_manifest()
        decision = manifest.get("rehearsal_decision")
        input_identity = {
            "execution_preflight_artifact_digest": context["execution_preflight_artifact_digest"],
            "execution_preflight_id": context["execution_preflight_id"],
            "rehearsal_policy_digest": digest(policy),
            "rehearsal_manifest_digest": digest(manifest),
            "rehearsal_decision_id": decision.get("decision_id") if decision else None,
            "rehearsal_decision_digest": digest(decision) if decision else None,
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
                raise IntegrationExecutionRehearsalBoundaryFailure(
                    "integration_execution_rehearsal_evaluation", "evaluation", self.failure_class
                )
            outcome = self._evaluate(context, policy, manifest)
            decision_binding = outcome["rehearsal_decision_binding"]
            semantic_attempt = {
                "execution_preflight_artifact_digest": context["execution_preflight_artifact_digest"],
                "execution_preflight_id": context["execution_preflight_id"],
                "plan_id": context["plan_id"],
                "plan_graph_digest": context["plan_graph_digest"],
                "rehearsal_policy_digest": input_identity["rehearsal_policy_digest"],
                "rehearsal_manifest_digest": input_identity["rehearsal_manifest_digest"],
                "rehearsal_decision_id": decision_binding.get("decision_id"),
                "rehearsal_decision_digest": decision_binding.get("record_digest"),
            }
            state["evaluation"] = {
                **deepcopy(context),
                **outcome,
                "input_identity": input_identity,
                "rehearsal_policy_version": policy["execution_rehearsal_policy_version"],
                "rehearsal_policy_id": policy["policy_id"],
                "rehearsal_manifest_id": manifest["manifest_id"],
                "execution_attempt_id": (
                    digest(semantic_attempt)
                    if outcome["classification"] == "rehearsal_complete"
                    else None
                ),
            }
        else:
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        receipts = self._ensure_receipts(evaluated, state)
        evaluated["rehearsal_receipts"] = receipts
        state["evaluation"]["receipt_ids"] = [x["receipt_id"] for x in receipts]
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
        return evaluated

    def _artifact_data(self, run: dict[str, Any], evaluated: dict[str, Any]) -> dict[str, Any]:
        decision = evaluated["rehearsal_decision_binding"]
        semantic_identity = {
            "execution_rehearsal_schema_version": EXECUTION_REHEARSAL_SCHEMA_VERSION,
            "execution_rehearsal_policy_version": evaluated["rehearsal_policy_version"],
            "execution_rehearsal_policy_id": evaluated["rehearsal_policy_id"],
            "execution_rehearsal_policy_digest": evaluated["input_identity"]["rehearsal_policy_digest"],
            "rehearsal_envelope_manifest_id": evaluated["rehearsal_manifest_id"],
            "rehearsal_envelope_manifest_digest": evaluated["input_identity"]["rehearsal_manifest_digest"],
            "rehearsal_decision_id": decision.get("decision_id"),
            "rehearsal_decision_digest": decision.get("record_digest"),
            "execution_preflight_artifact_digest": evaluated["execution_preflight_artifact_digest"],
            "execution_preflight_id": evaluated["execution_preflight_id"],
            "execution_preflight_classification": evaluated["execution_preflight_classification"],
            "execution_preflight_reason_codes": evaluated["execution_preflight_reason_codes"],
            "execution_preflight_policy_id": evaluated["execution_preflight_policy_id"],
            "execution_preflight_policy_digest": evaluated["execution_preflight_policy_digest"],
            "execution_envelope_manifest_id": evaluated["execution_envelope_manifest_id"],
            "execution_envelope_manifest_digest": evaluated["execution_envelope_manifest_digest"],
            "execution_envelope_decision_id": evaluated["execution_envelope_decision_id"],
            "execution_envelope_decision_digest": evaluated["execution_envelope_decision_digest"],
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
            "final_completion_receipt_digest": evaluated["final_completion_receipt_digest"],
            "canonical_chain_digest": evaluated["canonical_chain_digest"],
            "classification": evaluated["classification"],
            "classification_reason_codes": evaluated["classification_reason_codes"],
            "rehearsal_evidence_bindings": evaluated["rehearsal_evidence_bindings"],
            "execution_attempt_id": evaluated["execution_attempt_id"],
            "rehearsal_receipt_ids": [x["receipt_id"] for x in evaluated["rehearsal_receipts"]],
        }
        return {
            **semantic_identity,
            "execution_rehearsal_id": digest(semantic_identity),
            "rehearsal_receipts": deepcopy(evaluated["rehearsal_receipts"]),
            "rehearsal_receipt_count": len(evaluated["rehearsal_receipts"]),
            "execution_steps": deepcopy(evaluated["execution_steps"]),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_execution_rehearsal_only",
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
        self, existing: dict[str, Any] | None, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> None:
        if existing is None:
            return
        if existing.get("status") != "locked" or semantic_digest(existing) != existing.get("content_digest"):
            raise IntegrationExecutionRehearsalBoundaryFailure(
                "execution_rehearsal_validation",
                "execution_rehearsal_artifact",
                "cached execution rehearsal artifact is not valid and locked",
            )
        if existing.get("data") != self._artifact_data(run, evaluated):
            raise IntegrationExecutionRehearsalBoundaryFailure(
                "execution_rehearsal_validation",
                "execution_rehearsal_artifact",
                "cached execution rehearsal artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_rehearsal(self, run: dict[str, Any], evaluated: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "final_rehearsal_artifact" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("final_rehearsal_artifact", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationExecutionRehearsalBoundaryFailure(
                "integration_execution_rehearsal_artifact_assembly",
                "final_rehearsal_artifact",
                self.failure_class,
            )
        return self._artifact_data(run, evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionRehearsalError("final execution rehearsal artifact is not locked")
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionRehearsalError("final execution rehearsal artifact digest invalid")
        data = artifact.get("data") or {}
        for flag in (
            "production_action_authorized", "production_cutover_authorized",
            "legacy_decommission_authorized", "production_publication",
            "real_private_command_center_mutated", "public_site_mutated",
            "production_schedule_action", "subscriber_delivery_changed",
            "legacy_content_migrated", "readers_routed_to_greenfield",
            "legacy_repository_modified", "incremental_paid_dependency_added",
            "lifecycle_state_changed",
        ):
            if data.get(flag) is not False:
                raise IntegrationExecutionRehearsalError(f"execution rehearsal cannot authorize/mutate {flag}")
        if data.get("real_integration_steps_enabled") != 0 or data.get("real_integration_steps_executed") != 0:
            raise IntegrationExecutionRehearsalError("execution rehearsal cannot enable or execute real steps")
        steps = data.get("execution_steps") or []
        if len(steps) not in {0, 10}:
            raise IntegrationExecutionRehearsalError("execution rehearsal step inventory is incomplete")
        if any(item.get("enabled") is not False for item in steps):
            raise IntegrationExecutionRehearsalError("all real integration-plan steps must remain disabled")
        classification = data.get("classification")
        if classification == "rehearsal_complete":
            receipts = data.get("rehearsal_receipts") or []
            if data.get("execution_preflight_classification") != "execution_review_ready":
                raise IntegrationExecutionRehearsalError("only execution_review_ready can complete rehearsal")
            if not data.get("rehearsal_decision_id"):
                raise IntegrationExecutionRehearsalError("complete rehearsal requires separate decision")
            if len(receipts) != 10 or data.get("rehearsal_receipt_count") != 10:
                raise IntegrationExecutionRehearsalError("complete rehearsal requires exactly ten receipts")
            if any(
                x.get("execution_mode") != "noop"
                or x.get("external_execution_performed") is not False
                or x.get("real_service_contacted") is not False
                or x.get("side_effect_performed") is not False
                for x in receipts
            ):
                raise IntegrationExecutionRehearsalError("rehearsal receipts must prove no external execution")
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionRehearsalError("unsupported execution rehearsal classification")
        state = self._load_state()
        if classification == "blocked":
            state["metrics"]["blocked_classifications"] += 1
        elif classification == "rehearsal_complete":
            state["metrics"]["rehearsal_complete_classifications"] += 1
        else:
            state["metrics"]["invalid_classifications"] += 1
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
