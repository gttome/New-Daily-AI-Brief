from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import (
    ARTIFACT_DEPENDENCIES,
    COMPLETION_CONTRACT_VERSION,
    SCHEMA_VERSION,
)
from .operations import OperationsReconciliationPipeline, projection_currentness
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class CompletionError(ContractError):
    pass


class CompletionBoundaryFailure(CompletionError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"completion:{boundary_id}"


class FinalCompletionPipeline:
    """Iteration 9 deterministic synthetic/shadow final lifecycle closeout."""

    COMPLETION_SCOPE = "synthetic_shadow_validation"

    CANONICAL_CHAIN = (
        "discovery",
        "edition",
        "rating-contract",
        "media",
        "watchlist",
        "book-bridges",
        "images",
        "publication-bundle",
        "reader-render",
        "route-manifest",
        "release-package",
        "shadow-deployment",
        "live-verification",
        "book-change-evaluation",
        "command-center-projection",
        "projection-watermark",
    )

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        operations_fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_completion_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.operations_fixture_root = (
            Path(operations_fixture_root) if operations_fixture_root is not None else None
        )
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("completion:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration9-completion-state.json"
        self.metrics_path = self.store.run_dir / "iteration9-metrics.json"
        self.final_receipt_path = (
            self.store.run_dir / "iteration9-final-completion-receipt.json"
        )

    def _fail(self, boundary_type: str, boundary_id: str, message: str) -> None:
        state = self._load_state()
        state["metrics"]["validation_failures"] += 1
        self._save_state(state)
        self._write_metrics(state)
        raise CompletionBoundaryFailure(boundary_type, boundary_id, message)

    def _contract(self) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise CompletionError(
                "production completion is intentionally fail-closed: "
                "no approved zero-incremental-cost production cutover path is configured"
            )
        path = self.fixture_root / "completion-contract.json"
        if not path.exists():
            raise CompletionError(f"missing Iteration 9 completion contract fixture: {path}")
        contract = json.loads(path.read_text(encoding="utf-8"))
        checks = {
            "schema": contract.get("schema_version") == SCHEMA_VERSION,
            "contract": (
                contract.get("completion_contract_version")
                == COMPLETION_CONTRACT_VERSION
            ),
            "scope": contract.get("completion_scope") == self.COMPLETION_SCOPE,
            "shadow": contract.get("shadow_only") is True,
            "production": contract.get("production_authorized") is False,
            "cutover": contract.get("production_cutover_authorized") is False,
            "legacy": contract.get("legacy_decommission_authorized") is False,
            "private_site": (
                contract.get("real_command_center_mutation_authorized") is False
            ),
            "public_site": contract.get("public_site_mutation_authorized") is False,
        }
        if not all(checks.values()):
            raise CompletionError("unsupported or unsafe Iteration 9 completion contract")
        return contract

    def _load_state(self) -> dict[str, Any]:
        existing = self.store.read_json(self.state_path)
        if existing:
            if (
                existing.get("schema_version") != SCHEMA_VERSION
                or existing.get("edition_date") != self.edition_date
                or existing.get("mode") != self.mode
            ):
                raise CompletionError(
                    "Iteration 9 completion state is stale or schema-incompatible"
                )
            return existing
        return {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "attempts": {
                "completion_artifact": 0,
                "final_state_receipt": 0,
            },
            "metrics": {
                "validation_checks": 0,
                "validation_failures": 0,
                "completion_build_attempts": 0,
                "completion_build_retries": 0,
                "completion_reuse": 0,
                "final_transition_attempts": 0,
                "final_transition_retries": 0,
                "final_receipt_writes": 0,
                "final_receipt_reuse": 0,
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
                    "unrelated_final_completion_rewrite": 0,
                    "full_pipeline_restart": 0,
                },
            },
        }

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "recorded_at": utc_now(),
            "final_completion": deepcopy(state["metrics"]),
        }
        self.store._atomic_write(self.metrics_path, payload)

    def _require_locked(self, artifact_type: str) -> dict[str, Any]:
        record = self.store.load_artifact(artifact_type)
        if not record:
            self._fail(
                "completion_validation",
                artifact_type,
                f"locked {artifact_type} is missing",
            )
        if record.get("status") != "locked":
            self._fail(
                "completion_validation",
                artifact_type,
                f"{artifact_type} is not locked",
            )
        if record.get("schema_version") != SCHEMA_VERSION:
            self._fail(
                "completion_validation",
                artifact_type,
                f"{artifact_type} schema is incompatible",
            )
        if record.get("edition_date") != self.edition_date:
            self._fail(
                "completion_validation",
                artifact_type,
                f"{artifact_type} is stale or wrong-date",
            )
        if record.get("content_digest") != semantic_digest(record):
            self._fail(
                "completion_validation",
                artifact_type,
                f"{artifact_type} semantic digest mismatch",
            )
        expected_inputs = []
        for dependency in ARTIFACT_DEPENDENCIES[artifact_type]:
            dep = self.store.load_artifact(dependency)
            if not dep or dep.get("status") != "locked":
                self._fail(
                    "completion_validation",
                    artifact_type,
                    f"dependency {dependency} is not locked",
                )
            expected_inputs.append(dep["content_digest"])
        if sorted(record.get("input_digests", [])) != sorted(expected_inputs):
            self._fail(
                "completion_validation",
                artifact_type,
                f"{artifact_type} dependency binding mismatch",
            )
        return record

    def _operations(self) -> OperationsReconciliationPipeline:
        return OperationsReconciliationPipeline(
            self.store,
            self.edition_date,
            self.mode,
            self.operations_fixture_root,
        )

    def _validate_chain(self, run: dict[str, Any]) -> dict[str, Any]:
        self._contract()
        operations = self._operations()
        operations.validate_existing_projection_set()

        records = {
            artifact_type: self._require_locked(artifact_type)
            for artifact_type in self.CANONICAL_CHAIN
        }
        projection = records["command-center-projection"]
        watermark = records["projection-watermark"]
        receipt = self.store.read_json(operations.shadow_receipt_path)
        if receipt is None:
            self._fail(
                "completion_validation",
                "shadow_projection_receipt",
                "Iteration 8 shadow projection receipt is missing",
            )
        operations.validate_complete_reconciliation(projection, receipt, watermark)
        currentness = projection_currentness(watermark, projection, receipt)
        if currentness["status"] != "current":
            self._fail(
                "completion_validation",
                "projection_currentness",
                currentness["reason"],
            )

        bounded = projection["data"].get("bounded_lifecycle", {})
        if (
            bounded.get("state") != "OperationsReconciled"
            or bounded.get("completion_status") != "operations_reconciled_locked"
        ):
            self._fail(
                "completion_validation",
                "bounded_lifecycle",
                "Iteration 8 projection is not the locked OperationsReconciled state",
            )

        ops_receipt = (run.get("stage_receipts") or {}).get(
            "operations_reconciliation"
        )
        expected_ops_receipt = {
            "projection_digest": projection["content_digest"],
            "shadow_projection_receipt_digest": watermark["data"][
                "shadow_projection_receipt_digest"
            ],
            "projection_watermark_digest": watermark["content_digest"],
            "reconciliation_identity": watermark["data"][
                "reconciliation_identity"
            ],
            "scope": "shadow_only",
        }
        if ops_receipt != expected_ops_receipt:
            self._fail(
                "completion_validation",
                "operations_reconciliation_receipt",
                "run receipt does not bind the current Iteration 8 reconciliation identity",
            )

        verification = records["live-verification"]
        if (
            verification["data"].get("result") != "passed"
            or verification["data"].get("verification_scope") != "shadow_offline"
        ):
            self._fail(
                "completion_validation",
                "live-verification",
                "passing shadow_offline live verification is required",
            )

        evaluation = records["book-change-evaluation"]["data"]
        if (
            evaluation.get("all_items_evaluated") is not True
            or len(evaluation.get("item_evaluations", [])) != 10
            or len(evaluation.get("evaluated_item_ids", [])) != 10
        ):
            self._fail(
                "completion_validation",
                "book-change-evaluation",
                "exactly 10 successful explicit Iteration 7 evaluations are required",
            )

        state = self._load_state()
        state["metrics"]["validation_checks"] += len(self.CANONICAL_CHAIN) + 6
        self._save_state(state)
        self._write_metrics(state)
        return {
            "records": records,
            "projection": projection,
            "watermark": watermark,
            "shadow_receipt": receipt,
        }

    def _semantic_incident_summary(self, run: dict[str, Any]) -> dict[str, Any]:
        incident = self.store.load_incident()
        all_recovered = incident is None or incident.get("result") == "recovered"
        if not all_recovered or run.get("recovery_target") is not None:
            self._fail(
                "completion_validation",
                "incident_recovery",
                "unrecovered incident state cannot be finalized",
            )
        return {
            "recovery_model": "durable_targeted_boundary_resume",
            "all_recorded_incidents_recovered": True,
            "recovery_target_clear": True,
            "volatile_incident_counts_excluded_from_identity": True,
            "volatile_recovery_timestamps_excluded_from_identity": True,
        }

    def _anti_rework_identity(self, run: dict[str, Any]) -> dict[str, Any]:
        anti = run.get("anti_rework") or {}
        locked = int(anti.get("locked_stage_reexecutions", 0))
        restarts = int(anti.get("full_pipeline_restarts", 0))
        if locked != 0 or restarts != 0:
            self._fail(
                "completion_validation",
                "anti_rework",
                "locked Iterations 1-8 work was reexecuted or the full pipeline restarted",
            )
        return {
            "locked_iterations_1_8_stage_reexecutions": 0,
            "full_pipeline_restarts": 0,
            "locked_chain_reuse_required": True,
        }

    def _completion_data(
        self, run: dict[str, Any], context: dict[str, Any]
    ) -> dict[str, Any]:
        projection = context["projection"]
        watermark = context["watermark"]
        receipt = context["shadow_receipt"]
        p = projection["data"]
        complete_bindings = deepcopy(p["bindings"])
        complete_bindings["command-center-projection"] = projection[
            "content_digest"
        ]
        complete_bindings["projection-watermark"] = watermark["content_digest"]
        complete_bindings["shadow-projection-receipt"] = digest(receipt)
        complete_bindings["shadow-projection-output"] = receipt["output_digest"]

        return {
            "completion_event_id": f"dab-{self.edition_date}-{self.mode}:completion",
            "completion_contract_version": COMPLETION_CONTRACT_VERSION,
            "completion_scope": self.COMPLETION_SCOPE,
            "edition_date": self.edition_date,
            "run_id": f"dab-{self.edition_date}-{self.mode}",
            "canonical_chain_digest": p["canonical_chain_digest"],
            "complete_chain_bindings": complete_bindings,
            "projection_payload_digest": projection["content_digest"],
            "projection_watermark_digest": watermark["content_digest"],
            "projection_reconciliation_identity": watermark["data"][
                "reconciliation_identity"
            ],
            "shadow_projection_receipt_digest": digest(receipt),
            "shadow_projection_output_digest": receipt["output_digest"],
            "publication_bundle_digest": p["release"][
                "publication_bundle_digest"
            ],
            "reader_render_digest": p["release"]["reader_render_digest"],
            "route_manifest_digest": p["release"]["route_manifest_digest"],
            "release_package_digest": p["release"]["release_package_digest"],
            "shadow_deployment_digest": p["release"][
                "shadow_deployment_digest"
            ],
            "shadow_deployment_identity": p["release"][
                "shadow_deployment_identity"
            ],
            "live_verification_identity": {
                "digest": p["release"]["live_verification_digest"],
                "scope": p["release"]["verification_scope"],
                "result": p["release"]["verification_result"],
            },
            "book_change_evaluation_identity": {
                "digest": p["book_change_evaluation"]["evaluation_digest"],
                "explicit_item_evaluation_count": p[
                    "book_change_evaluation"
                ]["explicit_item_evaluation_count"],
                "proposal_count": p["book_change_evaluation"][
                    "proposal_count"
                ],
                "result_semantics": p["book_change_evaluation"][
                    "result_semantics"
                ],
            },
            "incident_recovery_summary": self._semantic_incident_summary(run),
            "anti_rework_state": self._anti_rework_identity(run),
            "final_state": "Complete",
            "final_status": "complete_locked",
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "real_command_center_mutated": False,
            "public_site_mutated": False,
            "production_publication": False,
            "production_schedule_mutated": False,
            "legacy_content_migrated": False,
            "volatile_completion_timestamps_excluded_from_identity": True,
            "volatile_elapsed_time_excluded_from_identity": True,
            "volatile_retry_counters_excluded_from_identity": True,
        }

    def build_completion(self, run: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        context = self._validate_chain(run)
        state = self._load_state()
        state["attempts"]["completion_artifact"] += 1
        state["metrics"]["completion_build_attempts"] += 1
        if state["attempts"]["completion_artifact"] > 1:
            state["metrics"]["completion_build_retries"] += 1
        self._save_state(state)
        if (
            self.failure_boundary_id == "completion_artifact"
            and not self._failure_fired
        ):
            self._failure_fired = True
            self._write_metrics(state)
            raise CompletionBoundaryFailure(
                "completion_artifact",
                "completion_artifact",
                self.failure_class,
            )
        data = self._completion_data(run, context)
        state["metrics"]["elapsed_ms"] = max(
            0, int((time.monotonic() - started) * 1000)
        )
        self._save_state(state)
        self._write_metrics(state)
        return data

    def _expected_final_receipt(
        self, completion: dict[str, Any]
    ) -> dict[str, Any]:
        data = completion["data"]
        return {
            "schema_version": SCHEMA_VERSION,
            "completion_contract_version": COMPLETION_CONTRACT_VERSION,
            "completion_event_id": data["completion_event_id"],
            "completion_artifact_digest": completion["content_digest"],
            "completion_scope": self.COMPLETION_SCOPE,
            "canonical_chain_digest": data["canonical_chain_digest"],
            "projection_watermark_digest": data[
                "projection_watermark_digest"
            ],
            "reconciliation_identity": data[
                "projection_reconciliation_identity"
            ],
            "transition": "OperationsReconciled->Complete",
            "transition_count": 1,
            "final_state": "Complete",
            "final_status": "complete_locked",
            "production_cutover_authorized": False,
            "legacy_decommission_authorized": False,
            "real_command_center_mutated": False,
            "public_site_mutated": False,
            "production_publication": False,
        }

    def validate_existing_completion_set(
        self, run: dict[str, Any]
    ) -> dict[str, Any] | None:
        context = self._validate_chain(run)
        completion = self.store.load_artifact("completion")
        receipt = self.store.read_json(self.final_receipt_path)
        if completion is None:
            if receipt is not None:
                self._fail(
                    "completion_validation",
                    "final_receipt",
                    "final completion receipt exists without the completion artifact",
                )
            return None

        completion = self._require_locked("completion")
        expected_data = self._completion_data(run, context)
        if completion.get("data") != expected_data:
            self._fail(
                "completion_validation",
                "completion_artifact",
                "cached final completion artifact is stale, corrupted, or binds different upstream identities",
            )
        if receipt is not None and receipt != self._expected_final_receipt(
            completion
        ):
            self._fail(
                "completion_validation",
                "final_receipt",
                "final completion receipt is stale or corrupted",
            )
        state = self._load_state()
        state["metrics"]["completion_reuse"] += 1
        if receipt is not None:
            state["metrics"]["final_receipt_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)
        return completion

    def finalize_completion(
        self, run: dict[str, Any], completion: dict[str, Any]
    ) -> dict[str, Any]:
        completion = self._require_locked("completion")
        expected = self._expected_final_receipt(completion)
        state = self._load_state()
        state["attempts"]["final_state_receipt"] += 1
        state["metrics"]["final_transition_attempts"] += 1
        if state["attempts"]["final_state_receipt"] > 1:
            state["metrics"]["final_transition_retries"] += 1
        existing = self.store.read_json(self.final_receipt_path)
        if existing is not None and existing != expected:
            self._fail(
                "completion_validation",
                "final_receipt",
                "existing final completion receipt does not match the locked completion artifact",
            )
        if existing is None:
            self.store._atomic_write(self.final_receipt_path, expected)
            state["metrics"]["final_receipt_writes"] += 1
        else:
            state["metrics"]["final_receipt_reuse"] += 1
        self._save_state(state)
        self._write_metrics(state)

        if (
            self.failure_boundary_id == "final_state_receipt"
            and not self._failure_fired
        ):
            self._failure_fired = True
            raise CompletionBoundaryFailure(
                "final_state_receipt",
                "final_state_receipt",
                self.failure_class,
            )
        return expected

    def validate_completed_run(self, run: dict[str, Any]) -> None:
        if (
            run.get("current_state") != "Complete"
            or run.get("completion_status") != "complete_locked"
        ):
            raise CompletionError(
                "completed synthetic/shadow run does not have bounded Iteration 9 final status"
            )
        completion = self.validate_existing_completion_set(run)
        if completion is None:
            self._fail(
                "completion_validation",
                "completion_artifact",
                "Complete state is missing the locked final completion artifact",
            )
        receipt = self.store.read_json(self.final_receipt_path)
        expected = self._expected_final_receipt(completion)
        if receipt != expected:
            self._fail(
                "completion_validation",
                "final_receipt",
                "Complete state is missing the deterministic final completion receipt",
            )
        if (run.get("stage_receipts") or {}).get("final_completion") != expected:
            self._fail(
                "completion_validation",
                "run_final_receipt",
                "run final-completion receipt does not match the deterministic receipt",
            )
