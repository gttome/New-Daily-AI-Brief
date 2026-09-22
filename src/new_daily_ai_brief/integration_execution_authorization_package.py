from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    EXECUTION_AUTHORIZATION_DECISION_POLICY_VERSION,
    EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION,
    EXECUTION_AUTHORIZATION_PACKAGE_POLICY_VERSION,
    EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION,
)
from .store import CanonicalStore, ContractError, digest, semantic_digest


class IntegrationExecutionAuthorizationPackageError(ContractError):
    pass


class IntegrationExecutionAuthorizationPackageBoundaryFailure(
    IntegrationExecutionAuthorizationPackageError
):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id


class ProductionIntegrationExecutionAuthorizationPackage:
    """Deterministic synthetic-only Iteration 18 authorization-package boundary."""

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

    DECISION_IDENTITY_FIELDS = (
        "authorization_decision_schema_version",
        "authorization_decision_policy_version",
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
        "provenance_validation_ids",
        "provenance_validation_digests",
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
        "classification",
        "classification_reason_codes",
    )

    TRANSITIVE_FIELDS = (
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
        failure_class: str = "synthetic_integration_execution_authorization_package_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = fixture_root
        self.failure_boundary_id = (
            failure_boundary_id.removeprefix("authorization_package:")
            if failure_boundary_id
            else None
        )
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "authorization-package-state.json"
        self.metrics_path = self.store.run_dir / "authorization-package-metrics.json"
        self.incident_path = self.store.run_dir / "authorization-package-incident.json"

    def _read_json_fixture(self, name: str, *, optional: bool = False) -> dict[str, Any] | None:
        if self.mode == "production" or self.fixture_root is None:
            raise IntegrationExecutionAuthorizationPackageError(
                "production authorization-package execution is intentionally unconfigured"
            )
        path = self.fixture_root / name
        if not path.exists():
            if optional:
                return None
            raise IntegrationExecutionAuthorizationPackageError(
                f"authorization-package fixture missing: {name}"
            )
        return json.loads(path.read_text(encoding="utf-8"))

    def _assert_authority_false(self, record: dict[str, Any], label: str) -> None:
        for flag in self.AUTHORITY_FLAGS:
            if record.get(flag) is not False:
                raise IntegrationExecutionAuthorizationPackageError(
                    f"{label} must keep {flag}=false"
                )
        if record.get("real_integration_steps_enabled", 0) != 0:
            raise IntegrationExecutionAuthorizationPackageError(
                f"{label} cannot enable real integration steps"
            )

    def _locked(self, artifact_type: str) -> dict[str, Any]:
        artifact = self.store.load_artifact(artifact_type)
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionAuthorizationPackageError(
                f"locked artifact missing: {artifact_type}"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionAuthorizationPackageError(
                f"locked artifact corrupted: {artifact_type}"
            )
        return artifact

    def _decision_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        return {key: deepcopy(data.get(key)) for key in self.DECISION_IDENTITY_FIELDS}

    def _source_validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"authorization-decision-verification-{position:02d}.json"

    def _load_source_validations(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        ids = deepcopy(data.get("provenance_validation_ids") or [])
        digests = deepcopy(data.get("provenance_validation_digests") or [])
        if data.get("classification") != "authorization_decision_ready":
            if ids or digests:
                raise IntegrationExecutionAuthorizationPackageError(
                    "blocked/invalid Iteration 17 cannot carry provenance validations"
                )
            return []
        if len(ids) != 10 or len(digests) != 10 or len(set(ids)) != 10:
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization_decision_ready requires ten unique provenance validations"
            )
        validations: list[dict[str, Any]] = []
        for position in range(1, 11):
            record = self.store.read_json(self._source_validation_path(position))
            if not record:
                raise IntegrationExecutionAuthorizationPackageError(
                    f"Iteration 17 provenance validation missing at position {position}"
                )
            if record.get("validation_id") != ids[position - 1]:
                raise IntegrationExecutionAuthorizationPackageError(
                    "Iteration 17 provenance validation order/id changed"
                )
            if digest(record) != digests[position - 1]:
                raise IntegrationExecutionAuthorizationPackageError(
                    "Iteration 17 provenance validation digest changed"
                )
            if (
                record.get("position") != position
                or record.get("noop_verified") is not True
                or record.get("side_effect_free_verified") is not True
            ):
                raise IntegrationExecutionAuthorizationPackageError(
                    "Iteration 17 provenance validation is unsafe"
                )
            validations.append(record)
        return validations

    def _context(self, run: dict[str, Any]) -> dict[str, Any]:
        if (
            run.get("current_state") != "Complete"
            or run.get("completion_status") != "complete_locked"
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "integration_execution_authorization_package_only requires Complete / complete_locked"
            )

        decision = self._locked("production-integration-execution-authorization-decision")
        dd = decision.get("data") or {}
        if (
            dd.get("authorization_decision_schema_version")
            != EXECUTION_AUTHORIZATION_DECISION_SCHEMA_VERSION
            or dd.get("authorization_decision_policy_version")
            != EXECUTION_AUTHORIZATION_DECISION_POLICY_VERSION
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "Iteration 17 authorization-decision version unsupported"
            )
        if digest(self._decision_identity(dd)) != dd.get("authorization_decision_id"):
            raise IntegrationExecutionAuthorizationPackageError(
                "Iteration 17 authorization-decision identity is corrupted"
            )
        if (
            dd.get("final_state") != "Complete"
            or dd.get("final_status") != "complete_locked"
            or dd.get("completion_scope")
            != "synthetic_shadow_execution_authorization_decision_only"
            or dd.get("synthetic_only") is not True
            or dd.get("real_integration_steps_enabled") != 0
            or dd.get("real_integration_steps_executed") != 0
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "Iteration 17 authorization-decision semantics are stale"
            )
        self._assert_authority_false(dd, "Iteration 17 authorization-decision")
        if any(x.get("enabled") is not False for x in dd.get("execution_steps") or []):
            raise IntegrationExecutionAuthorizationPackageError(
                "Iteration 17 real integration steps must remain disabled"
            )

        review = self._locked("production-integration-execution-authorization-review")
        rehearsal = self._locked("production-integration-execution-rehearsal")
        execution_preflight = self._locked("production-integration-execution-preflight")
        admission = self._locked("production-integration-admission")
        plan = self._locked("production-integration-plan")
        preflight = self._locked("production-integration-preflight")
        readiness = self._locked("readiness-admission")
        completion = self._locked("completion")

        checks = (
            (dd.get("authorization_review_artifact_digest"), review["content_digest"], "review digest"),
            (dd.get("authorization_review_id"), review["data"].get("authorization_review_id"), "review id"),
            (dd.get("execution_rehearsal_artifact_digest"), rehearsal["content_digest"], "rehearsal digest"),
            (dd.get("execution_rehearsal_id"), rehearsal["data"].get("execution_rehearsal_id"), "rehearsal id"),
            (dd.get("execution_attempt_id"), rehearsal["data"].get("execution_attempt_id"), "execution attempt"),
            (dd.get("execution_preflight_artifact_digest"), execution_preflight["content_digest"], "execution preflight digest"),
            (dd.get("execution_preflight_id"), execution_preflight["data"].get("execution_preflight_id"), "execution preflight id"),
            (dd.get("admission_artifact_digest"), admission["content_digest"], "admission digest"),
            (dd.get("admission_id"), admission["data"].get("admission_id"), "admission id"),
            (dd.get("plan_artifact_digest"), plan["content_digest"], "plan digest"),
            (dd.get("plan_id"), plan["data"].get("plan_id"), "plan id"),
            (dd.get("preflight_artifact_digest"), preflight["content_digest"], "preflight digest"),
            (dd.get("preflight_id"), preflight["data"].get("preflight_id"), "preflight id"),
            (dd.get("readiness_artifact_digest"), readiness["content_digest"], "readiness digest"),
            (dd.get("readiness_assessment_id"), readiness["data"].get("assessment_id"), "readiness id"),
            (dd.get("completion_artifact_digest"), completion["content_digest"], "completion digest"),
        )
        for actual, expected, label in checks:
            if actual != expected:
                raise IntegrationExecutionAuthorizationPackageError(
                    f"Iteration 17 transitive {label} binding changed"
                )

        plan_data = plan["data"]
        if dd.get("plan_graph_digest") != digest(plan_data.get("plan_steps") or []):
            raise IntegrationExecutionAuthorizationPackageError("Iteration 12 plan graph changed")
        if dd.get("dry_run_assertion_set_digest") != digest(
            plan_data.get("dry_run_assertion_set") or []
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "dry-run assertion set changed"
            )
        if dd.get("rollback_boundary_set_digest") != digest(
            plan_data.get("rollback_boundary_set") or []
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "rollback boundary set changed"
            )

        classification = dd.get("classification")
        if classification not in {"blocked", "authorization_decision_ready", "invalid"}:
            raise IntegrationExecutionAuthorizationPackageError(
                "unsupported Iteration 17 authorization-decision classification"
            )
        if classification == "authorization_decision_ready":
            if (
                not dd.get("separate_authorization_decision_id")
                or not dd.get("separate_authorization_decision_digest")
            ):
                raise IntegrationExecutionAuthorizationPackageError(
                    "authorization_decision_ready lacks separate decision identity"
                )
        source_validations = self._load_source_validations(dd)

        context = {
            "authorization_decision_artifact_digest": decision["content_digest"],
            "authorization_decision_id": dd["authorization_decision_id"],
            "authorization_decision_classification": classification,
            "authorization_decision_reason_codes": deepcopy(
                dd.get("classification_reason_codes") or []
            ),
            "authorization_decision_policy_id": dd.get("authorization_decision_policy_id"),
            "authorization_decision_policy_digest": dd.get("authorization_decision_policy_digest"),
            "authorization_decision_manifest_id": dd.get("authorization_decision_manifest_id"),
            "authorization_decision_manifest_digest": dd.get("authorization_decision_manifest_digest"),
            "separate_authorization_decision_id": dd.get("separate_authorization_decision_id"),
            "separate_authorization_decision_digest": dd.get("separate_authorization_decision_digest"),
            "source_provenance_validations": source_validations,
            "source_provenance_validation_ids": [x["validation_id"] for x in source_validations],
            "source_provenance_validation_digests": [digest(x) for x in source_validations],
            "source_provenance_validation_set_digest": digest(source_validations),
        }
        for field in self.TRANSITIVE_FIELDS:
            context[field] = deepcopy(dd.get(field))
        return context

    def _policy_manifest_package(
        self, context: dict[str, Any]
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any] | None]:
        policy = self._read_json_fixture("authorization-package-policy.json")
        manifest = self._read_json_fixture("authorization-package-manifest.json")
        package = self._read_json_fixture("authorization-package-record.json", optional=True)
        assert policy is not None and manifest is not None
        if (
            policy.get("schema_version") != EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION
            or policy.get("authorization_package_policy_version")
            != EXECUTION_AUTHORIZATION_PACKAGE_POLICY_VERSION
            or policy.get("policy_id")
            != "production-integration-execution-authorization-package-v1"
            or policy.get("synthetic_only") is not True
            or policy.get("real_authority_permitted") is not False
            or policy.get("zero_incremental_cost_required") is not True
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package policy unsupported"
            )
        if (
            manifest.get("schema_version") != EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION
            or manifest.get("authorization_package_manifest_version") != "1.0.0"
            or manifest.get("manifest_id")
            != "production-integration-execution-authorization-package-manifest-v1"
            or manifest.get("synthetic_only") is not True
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package manifest unsupported"
            )
        self._assert_authority_false(manifest, "authorization-package manifest")
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
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package evidence envelope incomplete"
            )
        if evidence["executor_declaration"] != {
            "real_executor_required": False,
            "real_executor_present": False,
            "real_executor_invocation_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationPackageError("executor declaration unsafe")
        if evidence["credential_declaration"] != {
            "credentials_required": False,
            "credentials_present": False,
            "credentials_use_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationPackageError("credential declaration unsafe")
        if evidence["target_declaration"] != {
            "scope": "synthetic_non_production",
            "real_target_present": False,
            "real_target_contact_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationPackageError("target declaration unsafe")
        if evidence["rollback_declaration"] != {
            "rollback_plan_bound": True,
            "rollback_execution_authorized": False,
        }:
            raise IntegrationExecutionAuthorizationPackageError("rollback declaration unsafe")
        if evidence["cost_declaration"] != {
            "incremental_paid_dependency_required": False,
            "zero_incremental_cost_approved": True,
        }:
            raise IntegrationExecutionAuthorizationPackageError(
                "zero-incremental-cost declaration missing"
            )
        expected_abort = {
            "identity_mismatch",
            "authority_flag_true",
            "cost_guard_failed",
            "provenance_validation_mismatch",
        }
        if set(evidence["stop_abort_conditions"]) != expected_abort:
            raise IntegrationExecutionAuthorizationPackageError(
                "stop/abort conditions incomplete"
            )
        self._assert_authority_false(evidence["authority_state"], "authority state")
        return policy, manifest, package

    def _package_record_id(self, package: dict[str, Any]) -> str:
        body = deepcopy(package)
        body.pop("package_record_id", None)
        return digest(body)

    def _package_binding(
        self,
        package: dict[str, Any] | None,
        context: dict[str, Any],
        manifest: dict[str, Any],
    ) -> tuple[dict[str, Any], str | None]:
        if package is None:
            return {
                "package_record_id": None,
                "package_record_digest": None,
            }, "AUTHORIZATION_PACKAGE_RECORD_MISSING"
        if (
            package.get("schema_version") != EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION
            or package.get("package_record_version") != "1.0.0"
            or package.get("record_kind")
            != "production-integration-execution-authorization-package-record"
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package record version unsupported"
            )
        if package.get("package_record_id") != self._package_record_id(package):
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package record identity changed"
            )
        self._assert_authority_false(package, "authorization-package record")
        if (
            package.get("synthetic_only") is not True
            or package.get("approved") is not True
            or package.get("decision")
            != "admit_synthetic_authorization_package_boundary"
            or package.get("scope") != "authorization_package_only"
            or package.get("grants_production_authority") is not False
            or package.get("zero_incremental_cost_approved") is not True
            or package.get("authorization_decision_id")
            != context["authorization_decision_id"]
            or package.get("authorization_decision_artifact_digest")
            != context["authorization_decision_artifact_digest"]
            or package.get("authorization_decision_policy_id")
            != context["authorization_decision_policy_id"]
            or package.get("authorization_decision_policy_digest")
            != context["authorization_decision_policy_digest"]
            or package.get("authorization_decision_manifest_id")
            != context["authorization_decision_manifest_id"]
            or package.get("authorization_decision_manifest_digest")
            != context["authorization_decision_manifest_digest"]
            or package.get("separate_authorization_decision_id")
            != context["separate_authorization_decision_id"]
            or package.get("separate_authorization_decision_digest")
            != context["separate_authorization_decision_digest"]
            or package.get("source_provenance_validation_set_digest")
            != context["source_provenance_validation_set_digest"]
            or package.get("authorization_package_manifest_id")
            != manifest["manifest_id"]
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package record binding changed"
            )
        return {
            "package_record_id": package["package_record_id"],
            "package_record_digest": digest(package),
        }, None

    def _evaluate(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        package: dict[str, Any] | None,
    ) -> dict[str, Any]:
        classification = context["authorization_decision_classification"]
        if classification == "invalid":
            return {
                "classification": "invalid",
                "classification_reason_codes": [
                    "ITERATION17_AUTHORIZATION_DECISION_INVALID",
                    *context["authorization_decision_reason_codes"],
                ],
                "authorization_package_binding": {
                    "package_record_id": None,
                    "package_record_digest": None,
                },
            }
        if classification == "blocked":
            return {
                "classification": "blocked",
                "classification_reason_codes": [
                    "ITERATION17_AUTHORIZATION_DECISION_BLOCKED",
                    *context["authorization_decision_reason_codes"],
                ],
                "authorization_package_binding": {
                    "package_record_id": None,
                    "package_record_digest": None,
                },
            }

        binding = manifest.get("authorization_decision_binding") or {}
        expected = {
            "binding_mode": "exact_locked_authorization_decision_artifact",
            "authorization_decision_artifact_digest": context["authorization_decision_artifact_digest"],
            "authorization_decision_id": context["authorization_decision_id"],
            "authorization_decision_policy_id": context["authorization_decision_policy_id"],
            "authorization_decision_policy_digest": context["authorization_decision_policy_digest"],
            "authorization_decision_manifest_id": context["authorization_decision_manifest_id"],
            "authorization_decision_manifest_digest": context["authorization_decision_manifest_digest"],
            "separate_authorization_decision_id": context["separate_authorization_decision_id"],
            "separate_authorization_decision_digest": context["separate_authorization_decision_digest"],
            "source_provenance_validation_ids": context["source_provenance_validation_ids"],
            "source_provenance_validation_digests": context["source_provenance_validation_digests"],
            "source_provenance_validation_set_digest": context["source_provenance_validation_set_digest"],
        }
        if binding != expected:
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package manifest binds a different Iteration 17 identity"
            )

        package_binding, reason = self._package_binding(package, context, manifest)
        if reason:
            return {
                "classification": "blocked",
                "classification_reason_codes": [reason],
                "authorization_package_binding": package_binding,
            }
        return {
            "classification": "authorization_package_ready",
            "classification_reason_codes": ["SYNTHETIC_AUTHORIZATION_PACKAGE_READY"],
            "authorization_package_binding": package_binding,
        }

    def _input_identity(
        self,
        context: dict[str, Any],
        policy: dict[str, Any],
        manifest: dict[str, Any],
        package: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "authorization_decision_artifact_digest": context[
                "authorization_decision_artifact_digest"
            ],
            "authorization_decision_id": context["authorization_decision_id"],
            "authorization_package_policy_digest": digest(policy),
            "authorization_package_manifest_digest": digest(manifest),
            "authorization_package_record_digest": digest(package) if package else None,
            "authorization_package_record_id": (
                package.get("package_record_id") if package else None
            ),
        }

    def _new_state(self, identity: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION,
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
                raise IntegrationExecutionAuthorizationPackageError(
                    "authorization-package state missing"
                )
            return self._new_state(identity)
        if (
            state.get("schema_version") != EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION
            or state.get("edition_date") != self.edition_date
            or state.get("mode") != self.mode
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package durable state version changed"
            )
        if identity is not None and state.get("input_identity") != identity:
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package durable state binds different inputs"
            )
        return state

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(
            self.metrics_path,
            {
                "schema_version": EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION,
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
                "schema_version": EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION,
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
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package incident binds different inputs"
            )
        incident["result"] = "recovered"
        self.store._atomic_write(self.incident_path, incident)

    def _validation_path(self, position: int) -> Path:
        return self.store.run_dir / f"authorization-package-validation-{position:02d}.json"

    def _validation_record(
        self, context: dict[str, Any], position: int, source: dict[str, Any]
    ) -> dict[str, Any]:
        body = {
            "schema_version": EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION,
            "authorization_decision_id": context["authorization_decision_id"],
            "position": position,
            "source_validation_id": source["validation_id"],
            "source_validation_digest": digest(source),
            "noop_verified": source.get("noop_verified"),
            "side_effect_free_verified": source.get("side_effect_free_verified"),
        }
        return {**body, "validation_id": digest(body)}

    def _ensure_provenance_validations(
        self, context: dict[str, Any], evaluated: dict[str, Any], state: dict[str, Any]
    ) -> list[dict[str, Any]]:
        if evaluated["classification"] != "authorization_package_ready":
            return []
        result: list[dict[str, Any]] = []
        for position, source in enumerate(
            context["source_provenance_validations"], start=1
        ):
            expected = self._validation_record(context, position, source)
            path = self._validation_path(position)
            existing = self.store.read_json(path)
            key = str(position)
            state["attempts"]["validations"].setdefault(key, 0)
            if existing is not None:
                if existing != expected:
                    raise IntegrationExecutionAuthorizationPackageError(
                        f"cached package provenance validation changed at position {position}"
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
                raise IntegrationExecutionAuthorizationPackageBoundaryFailure(
                    "authorization_package_provenance_validation",
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
        policy, manifest, package = self._policy_manifest_package(context)
        identity = self._input_identity(context, policy, manifest, package)
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
                raise IntegrationExecutionAuthorizationPackageBoundaryFailure(
                    "authorization_package_evaluation",
                    "evaluation",
                    self.failure_class,
                )
            outcome = self._evaluate(context, policy, manifest, package)
            state["evaluation"] = {
                **deepcopy(context),
                **outcome,
                "input_identity": deepcopy(identity),
                "authorization_package_policy_id": policy["policy_id"],
                "authorization_package_policy_version": policy[
                    "authorization_package_policy_version"
                ],
                "authorization_package_manifest_id": manifest["manifest_id"],
            }
            self._save_state(state)
        else:
            state["metrics"]["evaluation_reuse"] += 1
        evaluated = deepcopy(state["evaluation"])
        validations = self._ensure_provenance_validations(context, evaluated, state)
        evaluated["package_provenance_validations"] = validations
        state["evaluation"]["package_provenance_validation_ids"] = [
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
        package_binding = evaluated["authorization_package_binding"]
        identity = {
            "authorization_package_schema_version": EXECUTION_AUTHORIZATION_PACKAGE_SCHEMA_VERSION,
            "authorization_package_policy_version": evaluated[
                "authorization_package_policy_version"
            ],
            "authorization_package_policy_id": evaluated["authorization_package_policy_id"],
            "authorization_package_policy_digest": evaluated["input_identity"][
                "authorization_package_policy_digest"
            ],
            "authorization_package_manifest_id": evaluated[
                "authorization_package_manifest_id"
            ],
            "authorization_package_manifest_digest": evaluated["input_identity"][
                "authorization_package_manifest_digest"
            ],
            "separate_authorization_package_id": package_binding.get("package_record_id"),
            "separate_authorization_package_digest": package_binding.get(
                "package_record_digest"
            ),
            "authorization_decision_artifact_digest": evaluated[
                "authorization_decision_artifact_digest"
            ],
            "authorization_decision_id": evaluated["authorization_decision_id"],
            "authorization_decision_classification": evaluated[
                "authorization_decision_classification"
            ],
            "authorization_decision_reason_codes": evaluated[
                "authorization_decision_reason_codes"
            ],
            "authorization_decision_policy_id": evaluated["authorization_decision_policy_id"],
            "authorization_decision_policy_digest": evaluated[
                "authorization_decision_policy_digest"
            ],
            "authorization_decision_manifest_id": evaluated[
                "authorization_decision_manifest_id"
            ],
            "authorization_decision_manifest_digest": evaluated[
                "authorization_decision_manifest_digest"
            ],
            "separate_authorization_decision_id": evaluated[
                "separate_authorization_decision_id"
            ],
            "separate_authorization_decision_digest": evaluated[
                "separate_authorization_decision_digest"
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
            "package_provenance_validation_ids": [
                x["validation_id"] for x in evaluated["package_provenance_validations"]
            ],
            "package_provenance_validation_digests": [
                digest(x) for x in evaluated["package_provenance_validations"]
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
            "authorization_package_id": digest(identity),
            "real_integration_steps_enabled": 0,
            "real_integration_steps_executed": 0,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "completion_scope": "synthetic_shadow_execution_authorization_package_only",
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
            raise IntegrationExecutionAuthorizationPackageBoundaryFailure(
                "authorization_package_validation",
                "authorization_package_artifact",
                "cached authorization-package artifact invalid",
            )
        if existing.get("data") != self._artifact_data(evaluated):
            raise IntegrationExecutionAuthorizationPackageBoundaryFailure(
                "authorization_package_validation",
                "authorization_package_artifact",
                "cached authorization-package artifact binds different identities",
            )
        state = self._load_state(evaluated["input_identity"])
        assert state is not None
        state["metrics"]["artifact_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

    def build_authorization_package(
        self, run: dict[str, Any], evaluated: dict[str, Any]
    ) -> dict[str, Any]:
        state = self._load_state(evaluated["input_identity"])
        assert state is not None
        state["attempts"]["artifact_assembly"] += 1
        state["metrics"]["artifact_build_attempts"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id == "final_authorization_package_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._record_incident("final_authorization_package_artifact", state)
            self._write_metrics(state)
            raise IntegrationExecutionAuthorizationPackageBoundaryFailure(
                "authorization_package_artifact_assembly",
                "final_authorization_package_artifact",
                self.failure_class,
            )
        return self._artifact_data(evaluated)

    def finalize(self, artifact: dict[str, Any]) -> None:
        if not artifact or artifact.get("status") != "locked":
            raise IntegrationExecutionAuthorizationPackageError(
                "final authorization-package artifact is not locked"
            )
        if semantic_digest(artifact) != artifact.get("content_digest"):
            raise IntegrationExecutionAuthorizationPackageError(
                "final authorization-package artifact digest invalid"
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
                raise IntegrationExecutionAuthorizationPackageError(
                    f"authorization-package gate cannot authorize/mutate {flag}"
                )
        if (
            data.get("real_integration_steps_enabled") != 0
            or data.get("real_integration_steps_executed") != 0
            or any(x.get("enabled") is not False for x in data.get("execution_steps") or [])
        ):
            raise IntegrationExecutionAuthorizationPackageError(
                "authorization-package gate cannot enable/execute a real step"
            )
        classification = data.get("classification")
        if classification == "authorization_package_ready":
            if data.get("authorization_decision_classification") != "authorization_decision_ready":
                raise IntegrationExecutionAuthorizationPackageError(
                    "package readiness requires authorization_decision_ready upstream"
                )
            if not data.get("separate_authorization_package_id"):
                raise IntegrationExecutionAuthorizationPackageError(
                    "package readiness requires separate package identity"
                )
            if len(data.get("package_provenance_validation_ids") or []) != 10:
                raise IntegrationExecutionAuthorizationPackageError(
                    "package readiness requires ten provenance validations"
                )
        elif classification not in {"blocked", "invalid"}:
            raise IntegrationExecutionAuthorizationPackageError(
                "unsupported authorization-package classification"
            )
