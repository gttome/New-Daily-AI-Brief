from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import READINESS_POLICY_VERSION, READINESS_SCHEMA_VERSION
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class ReadinessError(ContractError):
    pass


class ReadinessBoundaryFailure(ReadinessError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"readiness:{boundary_id}"


class ProductionReadinessPipeline:
    """Deterministic, non-mutating Iteration 10 production-readiness assessment."""

    REQUIRED_PREREQUISITES = (
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

    REASON_CODES = {
        "cost_policy": ("COST_POLICY_EXPLICIT_AND_APPROVED", "COST_POLICY_APPROVAL_MISSING"),
        "production_discovery": (
            "DISCOVERY_ADAPTER_EXPLICIT_APPROVED_ZERO_COST",
            "DISCOVERY_ADAPTER_MISSING_OR_UNAPPROVED",
        ),
        "production_publication": (
            "PUBLICATION_PATH_AND_TARGET_EXPLICIT_APPROVED",
            "PUBLICATION_PATH_OR_TARGET_MISSING_OR_UNAPPROVED",
        ),
        "public_deployment_verification": (
            "PUBLIC_DEPLOYMENT_AND_VERIFICATION_EXPLICIT_APPROVED",
            "PUBLIC_DEPLOYMENT_OR_VERIFICATION_MISSING_OR_UNAPPROVED",
        ),
        "private_command_center": (
            "PRIVATE_COMMAND_CENTER_INTEGRATION_EXPLICIT_APPROVED",
            "PRIVATE_COMMAND_CENTER_INTEGRATION_MISSING_OR_UNAPPROVED",
        ),
        "production_schedules": (
            "SCHEDULE_POLICY_EXPLICIT_APPROVED",
            "SCHEDULE_POLICY_MISSING_OR_UNAPPROVED",
        ),
        "subscriber_delivery": (
            "SUBSCRIBER_DELIVERY_POLICY_EXPLICIT",
            "SUBSCRIBER_DELIVERY_POLICY_MISSING",
        ),
        "legacy_migration_cutover": (
            "MIGRATION_CUTOVER_PREREQUISITES_EXPLICIT",
            "MIGRATION_CUTOVER_PREREQUISITES_MISSING_OR_UNAPPROVED",
        ),
        "rollback_recovery": (
            "ROLLBACK_RECOVERY_EXPLICIT_APPROVED",
            "ROLLBACK_RECOVERY_MISSING_OR_UNAPPROVED",
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
        failure_class: str = "synthetic_readiness_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("readiness:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration10-readiness-state.json"
        self.metrics_path = self.store.run_dir / "iteration10-readiness-metrics.json"
        self.incident_path = self.store.run_dir / "iteration10-readiness-incident.json"
        self.final_receipt_path = self.store.run_dir / "iteration9-final-completion-receipt.json"

    def _read_json_fixture(self, name: str) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise ReadinessError(
                "production readiness is assessment-only and fail-closed: no approved "
                "repository-authoritative live capability declaration is configured"
            )
        path = self.fixture_root / name
        if not path.exists():
            raise ReadinessError(f"missing Iteration 10 readiness fixture: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _policy_and_capability(self) -> tuple[dict[str, Any], dict[str, Any]]:
        policy = self._read_json_fixture("readiness-policy.json")
        capability = self._read_json_fixture("capability-declaration.json")
        if (
            policy.get("schema_version") != READINESS_SCHEMA_VERSION
            or policy.get("readiness_policy_version") != READINESS_POLICY_VERSION
        ):
            raise ReadinessError("unsupported Iteration 10 readiness policy/schema version")
        if (
            capability.get("schema_version") != READINESS_SCHEMA_VERSION
            or capability.get("capability_declaration_version") != "1.0.0"
        ):
            raise ReadinessError("unsupported Iteration 10 capability declaration version")
        if tuple(policy.get("required_prerequisites") or ()) != self.REQUIRED_PREREQUISITES:
            raise ReadinessError("readiness prerequisite inventory is incomplete or ambiguous")
        if capability.get("synthetic_only") is not True:
            raise ReadinessError("Iteration 10 fixtures must remain synthetic_only")
        if capability.get("production_action_authorized") is not False:
            raise ReadinessError("Iteration 10 cannot authorize production action")
        return policy, capability

    def _completion_context(self, run: dict[str, Any]) -> dict[str, Any]:
        if run.get("current_state") != "Complete" or run.get("completion_status") != "complete_locked":
            raise ReadinessError("readiness_only requires Complete / complete_locked")
        completion = self.store.load_artifact("completion")
        if not completion or completion.get("status") != "locked":
            raise ReadinessError("locked Iteration 9 completion artifact is missing")
        if semantic_digest(completion) != completion.get("content_digest"):
            raise ReadinessError("locked Iteration 9 completion artifact is corrupted")
        data = completion.get("data") or {}
        if (
            data.get("final_state") != "Complete"
            or data.get("final_status") != "complete_locked"
            or data.get("completion_scope") != "synthetic_shadow_validation"
        ):
            raise ReadinessError("Iteration 9 completion semantics are stale or unsafe")
        receipt = self.store.read_json(self.final_receipt_path)
        if not receipt:
            raise ReadinessError("Iteration 9 final completion receipt is missing")
        if (
            receipt.get("completion_artifact_digest") != completion["content_digest"]
            or receipt.get("completion_event_id") != data.get("completion_event_id")
            or receipt.get("final_state") != "Complete"
            or receipt.get("final_status") != "complete_locked"
            or receipt.get("completion_scope") != "synthetic_shadow_validation"
        ):
            raise ReadinessError("Iteration 9 final completion receipt is mismatched or corrupted")
        if (run.get("stage_receipts") or {}).get("final_completion") != receipt:
            raise ReadinessError("run final-completion receipt does not match Iteration 9 receipt")
        return {
            "completion_digest": completion["content_digest"],
            "completion_event_id": data["completion_event_id"],
            "canonical_chain_digest": data["canonical_chain_digest"],
            "final_receipt_digest": digest(receipt),
        }

    def _new_state(self, input_identity: dict[str, str]) -> dict[str, Any]:
        return {
            "schema_version": READINESS_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "input_identity": input_identity,
            "attempts": {"policy_evaluation": 0, "artifact_assembly": 0},
            "evaluation": None,
            "metrics": {
                "validation_checks": 0,
                "validation_failures": 0,
                "policy_evaluation_attempts": 0,
                "policy_evaluation_reuse": 0,
                "artifact_build_attempts": 0,
                "artifact_reuse": 0,
                "blocked_classifications": 0,
                "admissible_classifications": 0,
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
                raise ReadinessError("readiness state identity is required")
            return self._new_state(input_identity)
        if (
            state.get("schema_version") != READINESS_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise ReadinessError("Iteration 10 readiness state is stale or schema-incompatible")
        if input_identity is not None and state.get("input_identity") != input_identity:
            raise ReadinessError(
                "cached readiness state binds different completion/policy/capability identities"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": READINESS_SCHEMA_VERSION,
                "edition_date": self.edition_date,
                "mode": self.mode,
                **deepcopy(state["metrics"]),
            },
        )

    def _record_incident(self, boundary_id: str, message: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.incident_path,
            {
                "schema_version": READINESS_SCHEMA_VERSION,
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
            raise ReadinessError("readiness recovery incident binds different input identity")
        incident["result"] = "recovered"
        incident["recovery_receipt"] = {
            "boundary_id": incident["boundary_id"],
            "input_identity": deepcopy(state["input_identity"]),
            "result": "recovered",
            "recovered_at": utc_now(),
        }
        state["metrics"]["recovery_attempts"] += 1
        self.store._atomic_write(self.incident_path, incident)

    def _is_approved(self, prerequisite: str, capability: dict[str, Any]) -> bool:
        item = capability.get(prerequisite) or {}
        if prerequisite == "cost_policy":
            return (
                item.get("approved") is True
                and item.get("separately_billed_openai_api_required") is False
                and item.get("paid_completion_or_storage_api_required") is False
                and item.get("paid_deployment_or_hosting_api_required") is False
                and item.get("other_incremental_paid_dependency_required") is False
            )
        if prerequisite == "production_discovery":
            return item.get("approved") is True and bool(item.get("adapter_id")) and item.get("zero_incremental_cost") is True
        if prerequisite == "production_publication":
            return item.get("approved") is True and bool(item.get("publication_path_id")) and bool(item.get("target_id"))
        if prerequisite == "public_deployment_verification":
            return item.get("approved") is True and bool(item.get("deployment_target_id")) and bool(item.get("verification_mechanism_id"))
        if prerequisite == "private_command_center":
            return item.get("approved") is True and bool(item.get("target_id")) and bool(item.get("projection_adapter_id")) and bool(item.get("privacy_boundary"))
        if prerequisite == "production_schedules":
            return item.get("approved") is True and bool(item.get("schedule_policy_id")) and bool(item.get("schedule_identities"))
        if prerequisite == "subscriber_delivery":
            return bool(item.get("policy_id")) and item.get("explicit") is True
        if prerequisite == "legacy_migration_cutover":
            return (
                item.get("prerequisites_approved") is True
                and bool(item.get("migration_plan_id"))
                and item.get("cutover_authorized") is False
                and item.get("legacy_decommission_authorized") is False
            )
        if prerequisite == "rollback_recovery":
            return item.get("approved") is True and bool(item.get("rollback_policy_id")) and bool(item.get("rollback_identity"))
        return False

    def _evaluate(self, capability: dict[str, Any]) -> dict[str, Any]:
        results: list[dict[str, str]] = []
        blockers: list[str] = []
        for prerequisite in self.REQUIRED_PREREQUISITES:
            approved = self._is_approved(prerequisite, capability)
            pass_code, block_code = self.REASON_CODES[prerequisite]
            reason = pass_code if approved else block_code
            results.append(
                {
                    "prerequisite": prerequisite,
                    "status": "satisfied" if approved else "blocked",
                    "reason_code": reason,
                }
            )
            if not approved:
                blockers.append(reason)
        return {
            "classification": "admissible" if not blockers else "blocked",
            "prerequisite_results": results,
            "blocker_reason_codes": blockers,
        }

    def prepare(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        context = self._completion_context(run)
        policy, capability = self._policy_and_capability()
        input_identity = {
            "completion_artifact_digest": context["completion_digest"],
            "final_completion_receipt_digest": context["final_receipt_digest"],
            "policy_digest": digest(policy),
            "capability_digest": digest(capability),
        }
        state = self._load_state(input_identity)
        state["metrics"]["validation_checks"] += 1
        if state.get("evaluation") is not None:
            state["metrics"]["policy_evaluation_reuse"] += 1
            state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._save_state(state)
            self._write_metrics(state)
            return deepcopy(state["evaluation"])

        state["attempts"]["policy_evaluation"] += 1
        state["metrics"]["policy_evaluation_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "policy_evaluation" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("policy_evaluation", self.failure_class, state)
            self._write_metrics(state)
            raise ReadinessBoundaryFailure(
                "readiness_policy_evaluation", "policy_evaluation", self.failure_class
            )

        evaluation = {
            **self._evaluate(capability),
            "readiness_policy_version": policy["readiness_policy_version"],
            "policy_id": policy["policy_id"],
            "profile_id": capability["profile_id"],
            "input_identity": input_identity,
            "completion_event_id": context["completion_event_id"],
            "canonical_chain_digest": context["canonical_chain_digest"],
        }
        state["evaluation"] = deepcopy(evaluation)
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state(state)
        self._write_metrics(state)
        return evaluation

    def _readiness_data(self, run: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        identity = evaluation["input_identity"]
        semantic_identity = {
            "readiness_schema_version": READINESS_SCHEMA_VERSION,
            "readiness_policy_version": evaluation["readiness_policy_version"],
            "policy_id": evaluation["policy_id"],
            "profile_id": evaluation["profile_id"],
            "completion_artifact_digest": identity["completion_artifact_digest"],
            "final_completion_receipt_digest": identity["final_completion_receipt_digest"],
            "canonical_chain_digest": evaluation["canonical_chain_digest"],
            "policy_digest": identity["policy_digest"],
            "capability_digest": identity["capability_digest"],
            "classification": evaluation["classification"],
            "prerequisite_results": evaluation["prerequisite_results"],
            "blocker_reason_codes": evaluation["blocker_reason_codes"],
        }
        return {
            **semantic_identity,
            "assessment_id": digest(semantic_identity),
            "completion_event_id": evaluation["completion_event_id"],
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
            raise ReadinessBoundaryFailure("readiness_validation", "readiness_artifact", "cached readiness artifact is not locked")
        if semantic_digest(existing) != existing.get("content_digest"):
            raise ReadinessBoundaryFailure("readiness_validation", "readiness_artifact", "cached readiness artifact is corrupted")
        if existing.get("data") != self._readiness_data(run, evaluation):
            raise ReadinessBoundaryFailure(
                "readiness_validation",
                "readiness_artifact",
                "cached readiness artifact binds different completion/policy/capability identities",
            )
        state = self._load_state(evaluation["input_identity"])
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_readiness(self, run: dict[str, Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state(evaluation["input_identity"])
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "final_readiness_artifact" and not self._failure_fired:
            self._failure_fired = True
            self._record_incident("final_readiness_artifact", self.failure_class, state)
            self._write_metrics(state)
            raise ReadinessBoundaryFailure(
                "readiness_artifact_assembly", "final_readiness_artifact", self.failure_class
            )
        return self._readiness_data(run, evaluation)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise ReadinessError("final readiness artifact is not locked")
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise ReadinessError("final readiness artifact digest is invalid")
        data = artifact.get("data") or {}
        if data.get("production_action_authorized") is not False:
            raise ReadinessError("readiness artifact cannot authorize production action")
        state = self._load_state()
        classification = data.get("classification")
        if classification == "blocked":
            state["metrics"]["blocked_classifications"] += 1
        elif classification == "admissible":
            state["metrics"]["admissible_classifications"] += 1
        else:
            state["metrics"]["invalid_classifications"] += 1
            self._save_state(state)
            self._write_metrics(state)
            raise ReadinessError("unsupported readiness classification")
        self._recover_incident_if_needed(state)
        self._save_state(state)
        self._write_metrics(state)
