from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    PREFLIGHT_POLICY_VERSION,
    PREFLIGHT_SCHEMA_VERSION,
    READINESS_POLICY_VERSION,
    READINESS_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class IntegrationPreflightError(ContractError):
    pass


class IntegrationPreflightBoundaryFailure(IntegrationPreflightError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"preflight:{boundary_id}"


class ProductionIntegrationPreflight:
    """Deterministic, non-mutating Iteration 11 prerequisite-resolution preflight."""

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

    RESOLUTION_CODES = {
        "canonical_chain_integrity": (
            "CANONICAL_CHAIN_RESOLUTION_BOUND",
            "CANONICAL_CHAIN_RESOLUTION_MISSING",
            "CANONICAL_CHAIN_RESOLUTION_INVALID",
        ),
        "cost_policy": (
            "COST_POLICY_RESOLUTION_BOUND",
            "COST_POLICY_RESOLUTION_MISSING",
            "COST_POLICY_RESOLUTION_INVALID",
        ),
        "production_discovery": (
            "PRODUCTION_DISCOVERY_RESOLUTION_BOUND",
            "PRODUCTION_DISCOVERY_RESOLUTION_MISSING",
            "PRODUCTION_DISCOVERY_RESOLUTION_INVALID",
        ),
        "production_publication": (
            "PRODUCTION_PUBLICATION_RESOLUTION_BOUND",
            "PRODUCTION_PUBLICATION_RESOLUTION_MISSING",
            "PRODUCTION_PUBLICATION_RESOLUTION_INVALID",
        ),
        "public_deployment_verification": (
            "PUBLIC_DEPLOYMENT_VERIFICATION_RESOLUTION_BOUND",
            "PUBLIC_DEPLOYMENT_VERIFICATION_RESOLUTION_MISSING",
            "PUBLIC_DEPLOYMENT_VERIFICATION_RESOLUTION_INVALID",
        ),
        "private_command_center": (
            "PRIVATE_COMMAND_CENTER_RESOLUTION_BOUND",
            "PRIVATE_COMMAND_CENTER_RESOLUTION_MISSING",
            "PRIVATE_COMMAND_CENTER_RESOLUTION_INVALID",
        ),
        "production_schedules": (
            "PRODUCTION_SCHEDULES_RESOLUTION_BOUND",
            "PRODUCTION_SCHEDULES_RESOLUTION_MISSING",
            "PRODUCTION_SCHEDULES_RESOLUTION_INVALID",
        ),
        "subscriber_delivery": (
            "SUBSCRIBER_DELIVERY_RESOLUTION_BOUND",
            "SUBSCRIBER_DELIVERY_RESOLUTION_MISSING",
            "SUBSCRIBER_DELIVERY_RESOLUTION_INVALID",
        ),
        "legacy_migration_cutover": (
            "LEGACY_MIGRATION_CUTOVER_RESOLUTION_BOUND",
            "LEGACY_MIGRATION_CUTOVER_RESOLUTION_MISSING",
            "LEGACY_MIGRATION_CUTOVER_RESOLUTION_INVALID",
        ),
        "rollback_recovery": (
            "ROLLBACK_RECOVERY_RESOLUTION_BOUND",
            "ROLLBACK_RECOVERY_RESOLUTION_MISSING",
            "ROLLBACK_RECOVERY_RESOLUTION_INVALID",
        ),
    }

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_integration_preflight_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("preflight:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration11-preflight-state.json"
        self.metrics_path = self.store.run_dir / "iteration11-preflight-metrics.json"
        self.incident_path = self.store.run_dir / "iteration11-preflight-incident.json"
        self.final_receipt_path = self.store.run_dir / "iteration9-final-completion-receipt.json"

    def _read_json_fixture(self, name: str) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationPreflightError(
                "production integration preflight is repository-evidence-only and fail-closed: "
                "no approved production resolution manifest is configured"
            )
        path = self.fixture_root / name
        if not path.exists():
            raise IntegrationPreflightError(f"missing Iteration 11 preflight fixture: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _policy_and_manifest(self) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self._read_json_fixture("preflight-policy.json")
        manifest = self._read_json_fixture("resolution-manifest.json")
        if (
            policy.get("schema_version") != PREFLIGHT_SCHEMA_VERSION
            or policy.get("preflight_policy_version") != PREFLIGHT_POLICY_VERSION
        ):
            raise IntegrationPreflightError("unsupported Iteration 11 preflight policy/schema version")
        if (
            manifest.get("schema_version") != PREFLIGHT_SCHEMA_VERSION
            or manifest.get("resolution_manifest_version") != "1.0.0"
        ):
            raise IntegrationPreflightError("unsupported Iteration 11 resolution manifest version")
        if tuple(policy.get("required_prerequisites") or ()) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPreflightError("preflight prerequisite inventory is incomplete or ambiguous")
        requirements = policy.get("evidence_requirements") or {}
        resolutions = manifest.get("resolutions") or {}
        if tuple(requirements.keys()) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPreflightError("preflight evidence-requirement inventory is incomplete or ambiguous")
        if tuple(resolutions.keys()) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPreflightError("resolution manifest inventory is incomplete or ambiguous")
        if manifest.get("synthetic_only") is not True:
            raise IntegrationPreflightError("Iteration 11 fixtures must remain synthetic_only")
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if manifest.get(flag) is not False:
                raise IntegrationPreflightError(f"Iteration 11 resolution manifest cannot authorize {flag}")
        return policy, manifest

    def _readiness_context(self, run: dict[str, Any]) -> dict[str, Any]:
        if run.get("current_state") != "Complete" or run.get("completion_status") != "complete_locked":
            raise IntegrationPreflightError(
                "integration_preflight_only requires Complete / complete_locked"
            )
        readiness = self.store.load_artifact("readiness-admission")
        if not readiness or readiness.get("status") != "locked":
            raise IntegrationPreflightError("locked Iteration 10 readiness artifact is missing")
        if semantic_digest(readiness) != readiness.get("content_digest"):
            raise IntegrationPreflightError("locked Iteration 10 readiness artifact is corrupted")

        data = readiness.get("data") or {}
        if (
            data.get("readiness_schema_version") != READINESS_SCHEMA_VERSION
            or data.get("readiness_policy_version") != READINESS_POLICY_VERSION
        ):
            raise IntegrationPreflightError("Iteration 10 readiness schema/policy version is unsupported")
        if (
            data.get("final_state") != "Complete"
            or data.get("final_status") != "complete_locked"
            or data.get("completion_scope") != "synthetic_shadow_validation"
            or data.get("synthetic_only") is not True
            or data.get("production_action_authorized") is not False
        ):
            raise IntegrationPreflightError("Iteration 10 readiness semantics are stale or unsafe")

        prereq_results = data.get("prerequisite_results") or []
        if tuple(item.get("prerequisite") for item in prereq_results) != self.REQUIRED_PREREQUISITES:
            raise IntegrationPreflightError("Iteration 10 readiness prerequisite inventory is incomplete")

        semantic_identity = {
            "readiness_schema_version": data.get("readiness_schema_version"),
            "readiness_policy_version": data.get("readiness_policy_version"),
            "policy_id": data.get("policy_id"),
            "profile_id": data.get("profile_id"),
            "completion_artifact_digest": data.get("completion_artifact_digest"),
            "final_completion_receipt_digest": data.get("final_completion_receipt_digest"),
            "canonical_chain_digest": data.get("canonical_chain_digest"),
            "policy_digest": data.get("policy_digest"),
            "capability_digest": data.get("capability_digest"),
            "classification": data.get("classification"),
            "prerequisite_results": prereq_results,
            "blocker_reason_codes": data.get("blocker_reason_codes") or [],
        }
        if digest(semantic_identity) != data.get("assessment_id"):
            raise IntegrationPreflightError("Iteration 10 readiness assessment identity is corrupted")

        completion = self.store.load_artifact("completion")
        if not completion or completion.get("status") != "locked":
            raise IntegrationPreflightError("locked Iteration 9 completion artifact is missing")
        if semantic_digest(completion) != completion.get("content_digest"):
            raise IntegrationPreflightError("locked Iteration 9 completion artifact is corrupted")
        completion_data = completion.get("data") or {}
        if readiness.get("input_digests") != [completion.get("content_digest")]:
            raise IntegrationPreflightError("Iteration 10 readiness dependency identity changed")
        if data.get("completion_artifact_digest") != completion.get("content_digest"):
            raise IntegrationPreflightError("Iteration 10 readiness completion identity changed")
        if data.get("completion_event_id") != completion_data.get("completion_event_id"):
            raise IntegrationPreflightError("Iteration 10 readiness completion event identity changed")
        if data.get("canonical_chain_digest") != completion_data.get("canonical_chain_digest"):
            raise IntegrationPreflightError("Iteration 10 readiness canonical chain identity changed")

        receipt = self.store.read_json(self.final_receipt_path)
        if not receipt or digest(receipt) != data.get("final_completion_receipt_digest"):
            raise IntegrationPreflightError("Iteration 10 readiness final receipt identity changed")

        return {
            "readiness_artifact_digest": readiness["content_digest"],
            "readiness_assessment_id": data["assessment_id"],
            "readiness_schema_version": data["readiness_schema_version"],
            "readiness_policy_version": data["readiness_policy_version"],
            "readiness_classification": data["classification"],
            "readiness_prerequisite_results": deepcopy(prereq_results),
            "completion_artifact_digest": completion["content_digest"],
            "final_completion_receipt_digest": data["final_completion_receipt_digest"],
            "canonical_chain_digest": data["canonical_chain_digest"],
        }

    def _new_state(self, input_identity: dict[str, str]) -> dict[str, Any]:
        return {
            "schema_version": PREFLIGHT_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": input_identity,
            "attempts": {"resolution_evaluation": 0, "artifact_assembly": 0},
            "evaluation": None,
            "metrics": {
                "validation_checks": 0,
                "validation_failures": 0,
                "resolution_evaluation_attempts": 0,
                "resolution_evaluation_reuse": 0,
                "resolution_evaluations_by_reason_code": {},
                "resolved_prerequisites": 0,
                "unresolved_prerequisites": 0,
                "invalid_prerequisites": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "unresolved_classifications": 0,
                "qualified_classifications": 0,
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
                raise IntegrationPreflightError("preflight state identity is required")
            return self._new_state(input_identity)
        if (
            state.get("schema_version") != PREFLIGHT_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationPreflightError("Iteration 11 preflight state is stale or schema-incompatible")
        if input_identity is not None and state.get("input_identity") != input_identity:
            raise IntegrationPreflightError(
                "cached preflight state binds different readiness/policy/manifest identities"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": PREFLIGHT_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                **deepcopy(state["metrics"]),
            },
        )

    def _record_incident(self, boundary_id: str, message: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": PREFLIGHT_SCHEMA_VERSION,
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
            raise IntegrationPreflightError("preflight recovery incident binds different input identity")
        incident["result"] = "recovered"
        incident["recovery_receipt"] = {
            "boundary_id": incident["boundary_id"],
            "input_identity": deepcopy(state["input_identity"]),
            "result": "recovered",
            "recovered_at": utc_now(),
        }
        state["metrics"]["recovery_attempts"] += 1
        self.store._atomic_write(self.incident_path, incident)

    def _evidence_valid(self, prerequisite: str, evidence: dict[str, Any]) -> bool:
        if evidence.get("synthetic_only") is not True:
            return False
        if evidence.get("production_action_authorized") is not False:
            return False
        if prerequisite == "cost_policy":
            return (
                evidence.get("record_kind") == "cost-policy-approval"
                and evidence.get("approved") is True
                and evidence.get("separately_billed_openai_api_required") is False
                and evidence.get("paid_completion_or_storage_api_required") is False
                and evidence.get("paid_deployment_or_hosting_api_required") is False
                and evidence.get("other_incremental_paid_dependency_required") is False
            )
        if prerequisite == "production_discovery":
            return (
                evidence.get("record_kind") == "production-discovery-adapter"
                and evidence.get("approved") is True
                and bool(evidence.get("adapter_id"))
                and evidence.get("zero_incremental_cost") is True
            )
        if prerequisite == "production_publication":
            return (
                evidence.get("record_kind") == "production-publication-path"
                and evidence.get("approved") is True
                and bool(evidence.get("publication_path_id"))
                and bool(evidence.get("target_id"))
            )
        if prerequisite == "public_deployment_verification":
            return (
                evidence.get("record_kind") == "public-deployment-verification"
                and evidence.get("approved") is True
                and bool(evidence.get("deployment_target_id"))
                and bool(evidence.get("verification_mechanism_id"))
            )
        if prerequisite == "private_command_center":
            return (
                evidence.get("record_kind") == "private-command-center-integration"
                and evidence.get("approved") is True
                and bool(evidence.get("target_id"))
                and bool(evidence.get("projection_adapter_id"))
                and bool(evidence.get("privacy_boundary"))
            )
        if prerequisite == "production_schedules":
            return (
                evidence.get("record_kind") == "production-schedule-policy"
                and evidence.get("approved") is True
                and bool(evidence.get("schedule_policy_id"))
                and bool(evidence.get("schedule_identities"))
            )
        if prerequisite == "subscriber_delivery":
            return (
                evidence.get("record_kind") == "subscriber-delivery-policy"
                and evidence.get("explicit") is True
                and bool(evidence.get("policy_id"))
            )
        if prerequisite == "legacy_migration_cutover":
            return (
                evidence.get("record_kind") == "legacy-migration-cutover-prerequisites"
                and evidence.get("prerequisites_approved") is True
                and bool(evidence.get("migration_plan_id"))
                and evidence.get("cutover_authorized") is False
                and evidence.get("legacy_decommission_authorized") is False
            )
        if prerequisite == "rollback_recovery":
            return (
                evidence.get("record_kind") == "rollback-recovery-policy"
                and evidence.get("approved") is True
                and bool(evidence.get("rollback_policy_id"))
                and bool(evidence.get("rollback_identity"))
            )
        return False

    def _evaluate(
        self,
        readiness: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        readiness_by_name = {
            item["prerequisite"]: item for item in readiness["readiness_prerequisite_results"]
        }
        results: list[dict[str, Any]] = []
        unresolved_codes: list[str] = []
        invalid_codes: list[str] = []

        for prerequisite in self.REQUIRED_PREREQUISITES:
            requirement = policy["evidence_requirements"][prerequisite]
            manifest_item = manifest["resolutions"][prerequisite] or {}
            readiness_item = readiness_by_name[prerequisite]
            resolved_code, unresolved_code, invalid_code = self.RESOLUTION_CODES[prerequisite]
            source = manifest_item.get("evidence_source")
            evidence = manifest_item.get("evidence")
            state = "unresolved"
            reason = unresolved_code
            record_id = None
            record_digest = None

            if source == "readiness_artifact":
                if readiness_item.get("status") == "satisfied" and evidence is None:
                    state = "resolved"
                    reason = resolved_code
                    record_id = readiness["readiness_assessment_id"]
                    record_digest = readiness["readiness_artifact_digest"]
                else:
                    state = "invalid"
                    reason = invalid_code
            elif source == "resolution_manifest":
                if not isinstance(evidence, dict):
                    state = "unresolved"
                    reason = unresolved_code
                else:
                    record_id = evidence.get("record_id")
                    record_digest = digest(evidence)
                    if not record_id or not self._evidence_valid(prerequisite, evidence):
                        state = "invalid"
                        reason = invalid_code
                    else:
                        state = "resolved"
                        reason = resolved_code
            elif source in (None, "none"):
                if evidence is not None:
                    state = "invalid"
                    reason = invalid_code
            else:
                state = "invalid"
                reason = invalid_code

            result = {
                "prerequisite": prerequisite,
                "readiness_status": readiness_item.get("status"),
                "readiness_reason_code": readiness_item.get("reason_code"),
                "required_resolution_evidence_type": requirement["evidence_type"],
                "explicit_approval_required": requirement.get("explicit_approval_required") is True,
                "paid_incremental_dependency_approval_required": requirement.get(
                    "paid_incremental_dependency_approval_required"
                )
                is True,
                "evidence_source": source or "none",
                "bound_repository_record_id": record_id,
                "bound_repository_record_digest": record_digest,
                "resolution_state": state,
                "resolution_reason_code": reason,
                "production_action_authorized": False,
            }
            results.append(result)
            if state == "unresolved":
                unresolved_codes.append(reason)
            elif state == "invalid":
                invalid_codes.append(reason)

        if invalid_codes:
            classification = "invalid"
        elif unresolved_codes:
            classification = "unresolved"
        else:
            classification = "qualified"
        return {
            "classification": classification,
            "resolution_results": results,
            "unresolved_reason_codes": unresolved_codes,
            "invalid_reason_codes": invalid_codes,
        }

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        readiness = self._readiness_context(run)
        policy, manifest = self._policy_and_manifest()
        input_identity = {
            "readiness_artifact_digest": readiness["readiness_artifact_digest"],
            "readiness_assessment_id": readiness["readiness_assessment_id"],
            "preflight_policy_digest": digest(policy),
            "resolution_manifest_digest": digest(manifest),
        }
        state = self._load_state(input_identity)
        state["metrics"]["validation_checks"] += 1
        if state.get("evaluation") is not None:
            state["metrics"]["resolution_evaluation_reuse"] += 1
            state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._save_state(state)
            self._write_metrics(state)
            return deepcopy(state["evaluation"])

        state["attempts"]["resolution_evaluation"] += 1
        state["metrics"]["resolution_evaluation_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "resolution_evaluation" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("resolution_evaluation", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationPreflightBoundaryFailure(
                "preflight_resolution_evaluation", "resolution_evaluation", self.failure_class
            )

        resolution = self._evaluate(readiness, policy, manifest)
        counts = {"resolved": 0, "unresolved": 0, "invalid": 0}
        by_reason = state["metrics"]["resolution_evaluations_by_reason_code"]
        for result in resolution["resolution_results"]:
            counts[result["resolution_state"]] += 1
            reason = result["resolution_reason_code"]
            by_reason[reason] = by_reason.get(reason, 0) + 1
        state["metrics"]["resolved_prerequisites"] = counts["resolved"]
        state["metrics"]["unresolved_prerequisites"] = counts["unresolved"]
        state["metrics"]["invalid_prerequisites"] = counts["invalid"]

        evaluation = {
            **resolution,
            "preflight_policy_version": policy["preflight_policy_version"],
            "policy_id": policy["policy_id"],
            "manifest_id": manifest["manifest_id"],
            "synthetic_only": manifest["synthetic_only"],
            "input_identity": input_identity,
            "readiness_schema_version": readiness["readiness_schema_version"],
            "readiness_policy_version": readiness["readiness_policy_version"],
            "readiness_classification": readiness["readiness_classification"],
            "completion_artifact_digest": readiness["completion_artifact_digest"],
            "final_completion_receipt_digest": readiness["final_completion_receipt_digest"],
            "canonical_chain_digest": readiness["canonical_chain_digest"],
        }
        state["evaluation"] = deepcopy(evaluation)
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state(state)
        self._write_metrics(state)
        return evaluation

    def _preflight_data(self, run: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        identity = evaluation["input_identity"]
        semantic_identity = {
            "preflight_schema_version": PREFLIGHT_SCHEMA_VERSION,
            "preflight_policy_version": evaluation["preflight_policy_version"],
            "policy_id": evaluation["policy_id"],
            "manifest_id": evaluation["manifest_id"],
            "readiness_artifact_digest": identity["readiness_artifact_digest"],
            "readiness_assessment_id": identity["readiness_assessment_id"],
            "readiness_schema_version": evaluation["readiness_schema_version"],
            "readiness_policy_version": evaluation["readiness_policy_version"],
            "readiness_classification": evaluation["readiness_classification"],
            "preflight_policy_digest": identity["preflight_policy_digest"],
            "resolution_manifest_digest": identity["resolution_manifest_digest"],
            "completion_artifact_digest": evaluation["completion_artifact_digest"],
            "final_completion_receipt_digest": evaluation["final_completion_receipt_digest"],
            "canonical_chain_digest": evaluation["canonical_chain_digest"],
            "classification": evaluation["classification"],
            "resolution_results": evaluation["resolution_results"],
            "unresolved_reason_codes": evaluation["unresolved_reason_codes"],
            "invalid_reason_codes": evaluation["invalid_reason_codes"],
        }
        return {
            **semantic_identity,
            "preflight_id": digest(semantic_identity),
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_validation",
            "synthetic_only": True,
            "production_action_authorized": False,
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "real_private_command_center_mutated": False,
            "public_site_mutated": False,
            "production_schedule_action": False,
            "subscriber_delivery_changed": False,
            "legacy_content_migrated": False,
            "production_publication": False,
            "lifecycle_state_changed": False,
        }

    def validate_existing(
        self,
        existing: dict[str, Any] | None,
        run: dict[str, Any],
        evaluation: dict[str, Any],
    ) -> None:
        if existing is None:
            return
        if existing.get("status") != "locked":
            raise IntegrationPreflightBoundaryFailure(
                "preflight_validation", "preflight_artifact", "cached preflight artifact is not locked"
            )
        if semantic_digest(existing) != existing.get("content_digest"):
            raise IntegrationPreflightBoundaryFailure(
                "preflight_validation", "preflight_artifact", "cached preflight artifact is corrupted"
            )
        if existing.get("data") != self._preflight_data(run, evaluation):
            raise IntegrationPreflightBoundaryFailure(
                "preflight_validation",
                "preflight_artifact",
                "cached preflight artifact binds different readiness/policy/manifest identities",
            )
        state = self._load_state(evaluation["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_preflight(self, run: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state(evaluation["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "final_preflight_artifact" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("final_preflight_artifact", self.failure_class, state)
            self._write_metrics(state)
            raise IntegrationPreflightBoundaryFailure(
                "preflight_artifact_assembly", "final_preflight_artifact", self.failure_class
            )
        return self._preflight_data(run, evaluation)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationPreflightError("final integration preflight artifact is not locked")
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationPreflightError("final integration preflight artifact digest is invalid")
        data = artifact.get("data") or {}
        for flag in (
            "production_action_authorized",
            "production_cutover_authorized",
            "legacy_decommission_authorized",
            "production_publication",
        ):
            if data.get(flag) is not False:
                raise IntegrationPreflightError(f"integration preflight cannot authorize {flag}")
        state = self._load_state()
        classification = data.get("classification")
        if classification == "unresolved":
            state["metrics"]["unresolved_classifications"] += 1
        elif classification == "qualified":
            state["metrics"]["qualified_classifications"] += 1
        elif classification == "invalid":
            state["metrics"]["invalid_classifications"] += 1
        else:
            raise IntegrationPreflightError("unsupported integration preflight classification")
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
