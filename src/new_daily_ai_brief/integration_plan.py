from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    PLAN_POLICY_VERSION,
    PLAN_SCHEMA_VERSION,
    PREFLIGHT_POLICY_VERSION,
    PREFLIGHT_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class IntegrationPlanError(ContractError):
    pass


class IntegrationPlanBoundaryFailure(IntegrationPlanError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"plan:{boundary_id}"


class ProductionIntegrationPlan:
    """Deterministic, non-mutating Iteration 12 integration-plan compiler."""

    REQUIRED_PREREQUISITES = (
        "canonical_chain_integrity",
        "cost_policy",
        "production_discovery",
        "production_publication",
        "public_deployment_verification",
        "private_command_center",
        "production_schedules",
        "subscriber_delivery",
        "legacy_migration_cutover",
        "rollback_recovery",
    )

    EXPLICIT_REFERENCE_KEYS = (
        "adapter_id",
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
        "migration_plan_id",
        "cutover_authorized",
        "legacy_decommission_authorized",
        "rollback_policy_id",
        "rollback_identity",
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
        failure_class: str = "synthetic_integration_plan_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("plan:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration12-plan-state.json"
        self.metrics_path = self.store.run_dir / "iteration12-plan-metrics.json"
        self.incident_path = self.store.run_dir / "iteration12-plan-incident.json"
        self.final_receipt_path = self.store.run_dir / "iteration9-final-completion-receipt.json"

    def _read_json_fixture(self, name: str) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationPlanError(
                "production integration planning is repository-evidence-only and fail-closed: "
                "no approved production plan policy/evidence binding is configured"
            )
        path = self.fixture_root / name
        if not path.exists():
            raise IntegrationPlanError(f"missing Iteration 12 plan fixture: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _policy_and_manifest(self) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self._read_json_fixture("integration-plan-policy.json")
        manifest = self._read_json_fixture("resolution-manifest.json")
        if (
            policy.get("schema_version") != PLAN_SCHEMA_VERSION
            or policy.get("integration_plan_policy_version") != PLAN_POLICY_VERSION
        ):
            raise IntegrationPlanError("unsupported Iteration 12 plan policy/schema version")
        if policy.get("synthetic_only") is not True:
            raise IntegrationPlanError("Iteration 12 plan policy must remain synthetic_only")
        if policy.get("production_action_authorized") is not False:
            raise IntegrationPlanError("Iteration 12 plan policy cannot authorize production action")
        if tuple(policy.get("required_prerequisites") or ()) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPlanError("plan prerequisite inventory is incomplete or ambiguous")
        steps = policy.get("step_templates") or {}
        if tuple(steps.keys()) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPlanError("plan step inventory is incomplete or ambiguous")
        seen: list[str] = []
        for prerequisite in self.REQUIRED_PREREQUISITES:
            template = steps[prerequisite]
            if template.get("prerequisite") != prerequisite:
                raise IntegrationPlanError("plan step prerequisite binding is invalid")
            step_id = template.get("step_id")
            if not step_id or step_id in seen:
                raise IntegrationPlanError("plan step IDs must be unique and non-empty")
            predecessors = template.get("predecessor_step_ids")
            assertions = template.get("dry_run_assertions")
            if not isinstance(predecessors, list) or any(p not in seen for p in predecessors):
                raise IntegrationPlanError("plan predecessor graph is invalid or non-topological")
            if not isinstance(assertions, list) or not assertions or not all(
                isinstance(x, str) and x for x in assertions
            ):
                raise IntegrationPlanError("plan dry-run assertion set is incomplete")
            if not template.get("rollback_boundary"):
                raise IntegrationPlanError("plan rollback boundary is missing")
            if template.get("production_action_authorized") is not False:
                raise IntegrationPlanError("plan template cannot authorize production action")
            seen.append(step_id)

        if (
            manifest.get("schema_version") != PREFLIGHT_SCHEMA_VERSION
            or manifest.get("resolution_manifest_version") != "1.0.0"
        ):
            raise IntegrationPlanError("unsupported bound Iteration 11 resolution manifest version")
        if manifest.get("synthetic_only") is not True:
            raise IntegrationPlanError("bound resolution manifest must remain synthetic_only")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if manifest.get(flag) is not False:
                raise IntegrationPlanError(f"bound resolution manifest cannot authorize {flag}")
        if tuple((manifest.get("resolutions") or {}).keys()) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPlanError("bound resolution manifest inventory is incomplete or ambiguous")
        return policy, manifest

    def _preflight_context(self, run: dict[str, Any]) -> dict[str, Any]:
        if run.get("current_state") != "Complete" or run.get("completion_status") != "complete_locked":
            raise IntegrationPlanError("integration_plan_only requires Complete / complete_locked")
        artifact = self.store.load_artifact("production-integration-preflight")
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationPlanError("locked Iteration 11 production-integration preflight is missing")
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationPlanError("locked Iteration 11 production-integration preflight is corrupted")
        data = artifact.get("data") or {}
        if (
            data.get("preflight_schema_version") != PREFLIGHT_SCHEMA_VERSION
            or data.get("preflight_policy_version") != PREFLIGHT_POLICY_VERSION
        ):
            raise IntegrationPlanError("Iteration 11 preflight schema/policy version is unsupported")
        if (
            data.get("final_state") != "Complete"
            or data.get("final_status") != "complete_locked"
            or data.get("completion_scope") != "synthetic_shadow_validation"
            or data.get("synthetic_only") is not True
        ):
            raise IntegrationPlanError("Iteration 11 preflight semantics are stale or unsafe")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if data.get(flag) is not False:
                raise IntegrationPlanError(f"Iteration 11 preflight cannot authorize {flag}")

        results = data.get("resolution_results") or []
        if tuple(item.get("prerequisite") for item in results) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPlanError("Iteration 11 preflight prerequisite inventory is incomplete")

        semantic_identity = {
            "preflight_schema_version": data.get("preflight_schema_version"),
            "preflight_policy_version": data.get("preflight_policy_version"),
            "policy_id": data.get("policy_id"),
            "manifest_id": data.get("manifest_id"),
            "readiness_artifact_digest": data.get("readiness_artifact_digest"),
            "readiness_assessment_id": data.get("readiness_assessment_id"),
            "readiness_schema_version": data.get("readiness_schema_version"),
            "readiness_policy_version": data.get("readiness_policy_version"),
            "readiness_classification": data.get("readiness_classification"),
            "preflight_policy_digest": data.get("preflight_policy_digest"),
            "resolution_manifest_digest": data.get("resolution_manifest_digest"),
            "completion_artifact_digest": data.get("completion_artifact_digest"),
            "final_completion_receipt_digest": data.get("final_completion_receipt_digest"),
            "canonical_chain_digest": data.get("canonical_chain_digest"),
            "classification": data.get("classification"),
            "resolution_results": results,
            "unresolved_reason_codes": data.get("unresolved_reason_codes") or [],
            "invalid_reason_codes": data.get("invalid_reason_codes") or [],
        }
        if digest(semantic_identity) != data.get("preflight_id"):
            raise IntegrationPlanError("Iteration 11 preflight identity is corrupted")

        readiness = self.store.load_artifact("readiness-admission")
        if not readiness or readiness.get("status") != "locked":
            raise IntegrationPlanError("bound Iteration 10 readiness artifact is missing")
        if semantic_digest(readiness) != readiness.get("content_digest"):
            raise IntegrationPlanError("bound Iteration 10 readiness artifact is corrupted")
        readiness_data = readiness.get("data") or {}
        if artifact.get("input_digests") != [readiness.get("content_digest")]:
            raise IntegrationPlanError("Iteration 11 preflight dependency identity changed")
        if data.get("readiness_artifact_digest") != readiness.get("content_digest"):
            raise IntegrationPlanError("Iteration 11 preflight readiness artifact identity changed")
        if data.get("readiness_assessment_id") != readiness_data.get("assessment_id"):
            raise IntegrationPlanError("Iteration 11 preflight readiness assessment identity changed")
        if data.get("completion_artifact_digest") != readiness_data.get("completion_artifact_digest"):
            raise IntegrationPlanError("Iteration 11 preflight completion identity changed")
        if data.get("final_completion_receipt_digest") != readiness_data.get(
            "final_completion_receipt_digest"
        ):
            raise IntegrationPlanError("Iteration 11 preflight final receipt identity changed")
        if data.get("canonical_chain_digest") != readiness_data.get("canonical_chain_digest"):
            raise IntegrationPlanError("Iteration 11 preflight canonical chain identity changed")

        completion = self.store.load_artifact("completion")
        if not completion or completion.get("status") != "locked":
            raise IntegrationPlanError("bound Iteration 9 completion artifact is missing")
        if semantic_digest(completion) != completion.get("content_digest"):
            raise IntegrationPlanError("bound Iteration 9 completion artifact is corrupted")
        if readiness.get("input_digests") != [completion.get("content_digest")]:
            raise IntegrationPlanError("Iteration 10 readiness dependency identity changed")
        completion_data = completion.get("data") or {}
        if readiness_data.get("completion_artifact_digest") != completion.get("content_digest"):
            raise IntegrationPlanError("Iteration 10 readiness completion artifact identity changed")
        if readiness_data.get("canonical_chain_digest") != completion_data.get(
            "canonical_chain_digest"
        ):
            raise IntegrationPlanError("Iteration 10 readiness canonical chain identity changed")

        final_receipt = self.store.read_json(self.final_receipt_path)
        if not final_receipt or digest(final_receipt) != data.get("final_completion_receipt_digest"):
            raise IntegrationPlanError("bound Iteration 9 final completion receipt identity changed")

        classification = data.get("classification")
        if classification not in {"unresolved", "qualified", "invalid"}:
            raise IntegrationPlanError("unsupported Iteration 11 preflight classification")

        return {
            "preflight_artifact_digest": artifact["content_digest"],
            "preflight_id": data["preflight_id"],
            "preflight_schema_version": data["preflight_schema_version"],
            "preflight_policy_version": data["preflight_policy_version"],
            "preflight_policy_digest": data["preflight_policy_digest"],
            "manifest_id": data["manifest_id"],
            "resolution_manifest_digest": data["resolution_manifest_digest"],
            "preflight_classification": classification,
            "resolution_results": deepcopy(results),
            "unresolved_reason_codes": deepcopy(data.get("unresolved_reason_codes") or []),
            "invalid_reason_codes": deepcopy(data.get("invalid_reason_codes") or []),
            "readiness_artifact_digest": data["readiness_artifact_digest"],
            "readiness_assessment_id": data["readiness_assessment_id"],
            "completion_artifact_digest": data["completion_artifact_digest"],
            "final_completion_receipt_digest": data["final_completion_receipt_digest"],
            "canonical_chain_digest": data["canonical_chain_digest"],
        }

    def _validate_manifest_binding(
        self, preflight: dict[str, Any], manifest: dict[str, Any]
    ) -> None:
        if digest(manifest) != preflight["resolution_manifest_digest"]:
            raise IntegrationPlanError("bound Iteration 11 resolution manifest identity changed")
        if manifest.get("manifest_id") != preflight["manifest_id"]:
            raise IntegrationPlanError("bound Iteration 11 resolution manifest ID changed")
        by_name = {x["prerequisite"]: x for x in preflight["resolution_results"]}
        for prerequisite in self.REQUIRED_PREREQUISITES:
            result = by_name[prerequisite]
            item = manifest["resolutions"][prerequisite] or {}
            source = item.get("evidence_source") or "none"
            evidence = item.get("evidence")
            if source != result.get("evidence_source"):
                raise IntegrationPlanError("preflight/manifest evidence source identity changed")
            if source == "resolution_manifest" and isinstance(evidence, dict):
                if result.get("bound_repository_record_id") != evidence.get("record_id"):
                    raise IntegrationPlanError("preflight/manifest repository record ID changed")
                if result.get("bound_repository_record_digest") != digest(evidence):
                    raise IntegrationPlanError("preflight/manifest repository record digest changed")
            elif source == "readiness_artifact":
                if evidence is not None:
                    raise IntegrationPlanError("readiness-bound resolution must not invent extra evidence")
                if result.get("bound_repository_record_id") != preflight["readiness_assessment_id"]:
                    raise IntegrationPlanError("readiness-bound repository record ID changed")
                if result.get("bound_repository_record_digest") != preflight[
                    "readiness_artifact_digest"
                ]:
                    raise IntegrationPlanError("readiness-bound repository record digest changed")
            elif evidence is not None:
                raise IntegrationPlanError("unresolved manifest entry cannot carry unbound evidence")

    def _new_state(self, input_identity: dict[str, str]) -> dict[str, Any]:
        return {
            "schema_version": PLAN_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": input_identity,
            "attempts": {"plan_compilation": 0, "artifact_assembly": 0},
            "compiled_plan": None,
            "metrics": {
                "plan_validation_checks": 0,
                "plan_validation_failures": 0,
                "plan_compilation_attempts": 0,
                "plan_compilation_reuse": 0,
                "plan_steps_compiled": 0,
                "plan_steps_blocked": 0,
                "plan_steps_invalid": 0,
                "dry_run_assertions_compiled": 0,
                "rollback_boundaries_compiled": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "blocked_classifications": 0,
                "planned_classifications": 0,
                "invalid_classifications": 0,
                "recovery_attempts": 0,
                "elapsed_ms": 0,
                "anti_rework": {
                    "discovery_reexecution": 0,
                    "editorial_reexecution": 0,
                    "media_reexecution": 0,
                    "watchlist_reexecution": 0,
                    "book_bridge_reexecution": 0,
                    "accepted_image_rework": 0,
                    "publication_bundle_rebuild": 0,
                    "reader_render_rebuild": 0,
                    "route_manifest_rebuild": 0,
                    "release_package_rebuild": 0,
                    "shadow_deployment_rewrite_or_redeployment": 0,
                    "valid_live_verification_rerun": 0,
                    "iteration7_item_reevaluation": 0,
                    "iteration7_evaluation_artifact_rebuild": 0,
                    "iteration8_projection_rebuild": 0,
                    "iteration8_shadow_projection_rewrite": 0,
                    "iteration8_watermark_rebuild": 0,
                    "iteration9_completion_rebuild": 0,
                    "iteration9_final_receipt_rewrite": 0,
                    "iteration10_readiness_evaluation_reexecution": 0,
                    "iteration10_readiness_artifact_rebuild": 0,
                    "iteration11_resolution_evaluation_reexecution": 0,
                    "iteration11_preflight_artifact_rebuild": 0,
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
                raise IntegrationPlanError("plan state identity is required")
            return self._new_state(input_identity)
        if (
            state.get("schema_version") != PLAN_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationPlanError("Iteration 12 plan state is stale or schema-incompatible")
        if input_identity is not None and state.get("input_identity") != input_identity:
            raise IntegrationPlanError(
                "cached plan state binds different preflight/policy/manifest identities"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": PLAN_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                **deepcopy(state["metrics"]),
            },
        )

    def _record_incident(self, boundary_id: str, message: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": PLAN_SCHEMA_VERSION,
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
            raise IntegrationPlanError("plan recovery incident binds different input identity")
        incident["result"] = "recovered"
        incident["recovery_receipt"] = {
            "boundary_id": incident["boundary_id"],
            "input_identity": deepcopy(state["input_identity"]),
            "result": "recovered",
            "recovered_at": utc_now(),
        }
        state["metrics"]["recovery_attempts"] += 1
        self.store._atomic_write(self.incident_path, incident)

    def _explicit_references(self, evidence: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(evidence, dict):
            return {}
        return {
            key: deepcopy(evidence[key])
            for key in self.EXPLICIT_REFERENCE_KEYS
            if key in evidence
        }

    def _compile(
        self,
        preflight: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        by_name = {x["prerequisite"]: x for x in preflight["resolution_results"]}
        steps: list[dict[str, Any]] = []
        assertion_set: list[dict[str, str]] = []
        rollback_set: list[dict[str, str]] = []

        for prerequisite in self.REQUIRED_PREREQUISITES:
            result = by_name[prerequisite]
            template = policy["step_templates"][prerequisite]
            manifest_item = manifest["resolutions"][prerequisite] or {}
            evidence = manifest_item.get("evidence")
            resolution_state = result.get("resolution_state")
            if resolution_state == "resolved":
                step_state = "planned"
                reason_code = "PLAN_STEP_EVIDENCE_BOUND"
            elif resolution_state == "unresolved":
                step_state = "blocked"
                reason_code = result.get("resolution_reason_code")
            elif resolution_state == "invalid":
                step_state = "invalid"
                reason_code = result.get("resolution_reason_code")
            else:
                raise IntegrationPlanError("unsupported preflight resolution state")

            refs = self._explicit_references(evidence)
            if manifest_item.get("evidence_source") == "readiness_artifact":
                refs = {
                    "readiness_assessment_id": preflight["readiness_assessment_id"],
                    "readiness_artifact_digest": preflight["readiness_artifact_digest"],
                }

            step = {
                "step_id": template["step_id"],
                "prerequisite": prerequisite,
                "step_state": step_state,
                "reason_code": reason_code,
                "bound_evidence_source": result.get("evidence_source"),
                "bound_evidence_record_id": result.get("bound_repository_record_id"),
                "bound_evidence_record_digest": result.get("bound_repository_record_digest"),
                "predecessor_step_ids": deepcopy(template["predecessor_step_ids"]),
                "dry_run_assertions": deepcopy(template["dry_run_assertions"]),
                "rollback_boundary": template["rollback_boundary"],
                "explicit_references": refs,
                "production_action_authorized": False,
            }
            steps.append(step)
            assertion_set.extend(
                {"step_id": step["step_id"], "assertion": assertion}
                for assertion in step["dry_run_assertions"]
            )
            rollback_set.append(
                {"step_id": step["step_id"], "rollback_boundary": step["rollback_boundary"]}
            )

        preflight_classification = preflight["preflight_classification"]
        if preflight_classification == "invalid":
            classification = "invalid"
            reason_codes = preflight["invalid_reason_codes"] or ["PREFLIGHT_INVALID"]
        elif preflight_classification == "unresolved":
            classification = "blocked"
            reason_codes = deepcopy(preflight["unresolved_reason_codes"])
        elif preflight_classification == "qualified":
            if not all(step["step_state"] == "planned" for step in steps):
                classification = "invalid"
                reason_codes = ["QUALIFIED_PREFLIGHT_PLAN_BINDING_INCOMPLETE"]
            else:
                classification = "planned"
                reason_codes = ["PLAN_INPUTS_COMPLETE_SYNTHETIC_ONLY"]
        else:
            raise IntegrationPlanError("unsupported preflight classification")

        if classification == "planned" and preflight_classification != "qualified":
            raise IntegrationPlanError("unresolved/invalid preflight cannot silently become planned")

        return {
            "classification": classification,
            "classification_reason_codes": reason_codes,
            "steps": steps,
            "dry_run_assertion_set": assertion_set,
            "rollback_boundary_set": rollback_set,
        }

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        preflight = self._preflight_context(run)
        policy, manifest = self._policy_and_manifest()
        self._validate_manifest_binding(preflight, manifest)
        input_identity = {
            "preflight_artifact_digest": preflight["preflight_artifact_digest"],
            "preflight_id": preflight["preflight_id"],
            "plan_policy_digest": digest(policy),
            "resolution_manifest_digest": preflight["resolution_manifest_digest"],
        }
        state = self._load_state(input_identity)
        state["metrics"]["plan_validation_checks"] += 1
        if state.get("compiled_plan") is not None:
            state["metrics"]["plan_compilation_reuse"] += 1
            state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._save_state(state)
            self._write_metrics(state)
            return deepcopy(state["compiled_plan"])

        state["attempts"]["plan_compilation"] += 1
        state["metrics"]["plan_compilation_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "compilation" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("compilation", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationPlanBoundaryFailure(
                "integration_plan_compilation", "compilation", self.failure_class
            )

        compiled = self._compile(preflight, policy, manifest)
        state["compiled_plan"] = {
            **compiled,
            "plan_policy_version": policy["integration_plan_policy_version"],
            "plan_policy_id": policy["policy_id"],
            "input_identity": input_identity,
            "preflight_schema_version": preflight["preflight_schema_version"],
            "preflight_policy_version": preflight["preflight_policy_version"],
            "preflight_classification": preflight["preflight_classification"],
            "readiness_artifact_digest": preflight["readiness_artifact_digest"],
            "readiness_assessment_id": preflight["readiness_assessment_id"],
            "completion_artifact_digest": preflight["completion_artifact_digest"],
            "final_completion_receipt_digest": preflight["final_completion_receipt_digest"],
            "canonical_chain_digest": preflight["canonical_chain_digest"],
        }
        planned_count = sum(x["step_state"] == "planned" for x in compiled["steps"])
        blocked_count = sum(x["step_state"] == "blocked" for x in compiled["steps"])
        invalid_count = sum(x["step_state"] == "invalid" for x in compiled["steps"])
        state["metrics"]["plan_steps_compiled"] = planned_count
        state["metrics"]["plan_steps_blocked"] = blocked_count
        state["metrics"]["plan_steps_invalid"] = invalid_count
        state["metrics"]["dry_run_assertions_compiled"] = len(compiled["dry_run_assertion_set"])
        state["metrics"]["rollback_boundaries_compiled"] = len(compiled["rollback_boundary_set"])
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state(state)
        self._write_metrics(state)
        return deepcopy(state["compiled_plan"])

    def _plan_data(self, run: dict[str, Any], compiled: dict[str, Any]) -> dict[str, Any]:
        identity = compiled["input_identity"]
        semantic_identity = {
            "plan_schema_version": PLAN_SCHEMA_VERSION,
            "plan_policy_version": compiled["plan_policy_version"],
            "plan_policy_id": compiled["plan_policy_id"],
            "plan_policy_digest": identity["plan_policy_digest"],
            "preflight_artifact_digest": identity["preflight_artifact_digest"],
            "preflight_id": identity["preflight_id"],
            "preflight_schema_version": compiled["preflight_schema_version"],
            "preflight_policy_version": compiled["preflight_policy_version"],
            "preflight_classification": compiled["preflight_classification"],
            "resolution_manifest_digest": identity["resolution_manifest_digest"],
            "readiness_artifact_digest": compiled["readiness_artifact_digest"],
            "readiness_assessment_id": compiled["readiness_assessment_id"],
            "completion_artifact_digest": compiled["completion_artifact_digest"],
            "final_completion_receipt_digest": compiled["final_completion_receipt_digest"],
            "canonical_chain_digest": compiled["canonical_chain_digest"],
            "classification": compiled["classification"],
            "classification_reason_codes": compiled["classification_reason_codes"],
            "plan_steps": compiled["steps"],
            "dry_run_assertion_set": compiled["dry_run_assertion_set"],
            "rollback_boundary_set": compiled["rollback_boundary_set"],
        }
        return {
            **semantic_identity,
            "plan_id": digest(semantic_identity),
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_plan_only",
            "synthetic_only": True,
            "production_action_authorized": False,
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "real_private_command_center_mutated": False,
            "public_site_mutated": False,
            "production_schedule_action": False,
            "subscriber_delivery_changed": False,
            "legacy_content_migrated": False,
            "readers_routed_to_greenfield": False,
            "production_publication": False,
            "legacy_repository_modified": False,
            "incremental_paid_dependency_added": False,
            "lifecycle_state_changed": False,
        }

    def validate_existing(
        self,
        existing: dict[str, Any] | None,
        run: dict[str, Any],
        compiled: dict[str, Any],
    ) -> None:
        if existing is None:
            return
        if existing.get("status") != "locked":
            raise IntegrationPlanBoundaryFailure(
                "plan_validation", "plan_artifact", "cached plan artifact is not locked"
            )
        if semantic_digest(existing) != existing.get("content_digest"):
            raise IntegrationPlanBoundaryFailure(
                "plan_validation", "plan_artifact", "cached plan artifact is corrupted"
            )
        if existing.get("data") != self._plan_data(run, compiled):
            raise IntegrationPlanBoundaryFailure(
                "plan_validation",
                "plan_artifact",
                "cached plan artifact binds different preflight/policy identities",
            )
        state = self._load_state(compiled["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_plan(self, run: dict[str, Any], compiled: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state(compiled["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "final_plan_artifact" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("final_plan_artifact", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationPlanBoundaryFailure(
                "integration_plan_artifact_assembly", "final_plan_artifact", self.failure_class
            )
        return self._plan_data(run, compiled)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationPlanError("final production integration plan artifact is not locked")
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationPlanError("final production integration plan artifact digest is invalid")
        data = artifact.get("data") or {}
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if data.get(flag) is not False:
                raise IntegrationPlanError(f"integration plan cannot authorize {flag}")
        if data.get("classification") == "planned" and data.get("preflight_classification") != "qualified":
            raise IntegrationPlanError("unresolved/invalid preflight cannot silently become planned")
        state = self._load_state()
        classification = data.get("classification")
        if classification == "blocked":
            state["metrics"]["blocked_classifications"] += 1
        elif classification == "planned":
            state["metrics"]["planned_classifications"] += 1
        elif classification == "invalid":
            state["metrics"]["invalid_classifications"] += 1
        else:
            raise IntegrationPlanError("unsupported integration plan classification")
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
