from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any, Callable

from .contracts import (
    ARTIFACT_DEPENDENCIES,
    LEGAL_TRANSITIONS,
    MANDATORY_COMPLETION_RECEIPTS,
    PROJECTION_SCHEMA_VERSION,
    RATING_CONTRACT_VERSION,
    RUN_SCHEMA_VERSION,
    SCHEMA_VERSION,
    FailureInjection,
)
from .store import CanonicalStore, ContractError, digest, utc_now


class IllegalTransition(ContractError):
    pass


class SyntheticFailure(RuntimeError):
    pass


class IncompleteCompletion(ContractError):
    pass


class RunEngine:
    def __init__(
        self,
        state_root: Path | str,
        edition_date: str,
        mode: str = "synthetic",
        owner: str = "orchestrator",
        failure_injection: FailureInjection | None = None,
    ):
        if mode not in {"synthetic", "shadow", "production"}:
            raise ValueError(f"unsupported mode: {mode}")
        self.store = CanonicalStore(Path(state_root), edition_date, mode)
        self.edition_date = edition_date
        self.mode = mode
        self.run_id = f"dab-{edition_date}-{mode}"
        self.owner = owner
        self.failure_injection = failure_injection
        self._injection_fired = False

    def _new_run(self) -> dict[str, Any]:
        now = utc_now()
        return {
            "schema_version": RUN_SCHEMA_VERSION,
            "run_id": self.run_id,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "current_state": "Ready",
            "completion_status": "in_progress",
            "created_at": now,
            "updated_at": now,
            "stage_executions": {},
            "stage_receipts": {},
            "recovery_target": None,
            "incident_count": 0,
            "manual_intervention": False,
            "anti_rework": {
                "locked_stage_reexecutions": 0,
                "full_pipeline_restarts": 0,
                "artifact_reuses": 0,
                "artifact_rebuilds": 0,
            },
        }

    def load_or_create(self) -> dict[str, Any]:
        run = self.store.load_run()
        if run:
            return run
        run = self._new_run()
        self.store.write_run(run)
        return run

    def transition(self, run: dict[str, Any], target: str) -> None:
        current = run["current_state"]
        if target not in LEGAL_TRANSITIONS[current]:
            raise IllegalTransition(f"illegal transition {current} -> {target}")
        run["current_state"] = target
        self.store.write_run(run)

    def _count_stage(self, run: dict[str, Any], stage: str) -> None:
        run["stage_executions"][stage] = run["stage_executions"].get(stage, 0) + 1
        self.store.write_run(run)

    def _input_digests(self, artifact_type: str) -> list[str]:
        values: list[str] = []
        for dependency in ARTIFACT_DEPENDENCIES[artifact_type]:
            record = self.store.load_artifact(dependency)
            if not record or record.get("status") != "locked":
                raise ContractError(f"dependency {dependency} is not locked for {artifact_type}")
            values.append(record["content_digest"])
        return values

    def _ensure_artifact(
        self,
        run: dict[str, Any],
        artifact_type: str,
        stage: str,
        data_factory: Callable[[], dict[str, Any]],
    ) -> dict[str, Any]:
        existing = self.store.load_artifact(artifact_type)
        if existing and existing.get("status") == "locked":
            current_inputs = sorted(self._input_digests(artifact_type))
            if sorted(existing.get("input_digests", [])) == current_inputs:
                run["anti_rework"]["artifact_reuses"] += 1
                self.store.write_run(run)
                return existing
            self.store.invalidate(artifact_type, "dependency_digest_changed")
        self._count_stage(run, stage)
        input_digests = self._input_digests(artifact_type)
        artifact, reused = self.store.lock_artifact(
            artifact_type=artifact_type,
            artifact_id=f"{self.run_id}:{artifact_type}",
            data=data_factory(),
            produced_by_stage=stage,
            input_digests=input_digests,
        )
        if reused:
            run["anti_rework"]["artifact_reuses"] += 1
        else:
            run["anti_rework"]["artifact_rebuilds"] += 1
        self.store.write_run(run)
        return artifact

    def _synthetic_edition(self) -> dict[str, Any]:
        categories = [
            "agents_non_technical_people",
            "agents_non_technical_people",
            "applied_genai_knowledge_workers",
            "applied_genai_knowledge_workers",
            "technical_ai_engineering",
            "technical_ai_engineering",
        ]
        stories = []
        for index, category in enumerate(categories, start=1):
            stories.append({
                "story_id": f"synthetic-story-{index}",
                "category_id": category,
                "title": f"Synthetic story {index}",
                "agent_skills": index == 1,
                "presentation_position": index,
            })
        return {
            "stories": stories,
            "allocation": {"agents": 2, "applied": 2, "technical": 2},
            "agent_skills_count": 1,
            "presentation_order": [
                "agents_non_technical_people",
                "applied_genai_knowledge_workers",
                "technical_ai_engineering",
            ],
        }

    def _synthetic_media(self) -> dict[str, Any]:
        return {
            "videos": [
                {"media_id": "video-1", "verified": True},
                {"media_id": "video-2", "verified": True},
            ],
            "podcasts": [
                {"media_id": "podcast-1", "verified": True},
                {"media_id": "podcast-2", "verified": True},
            ],
            "preflight": "passed",
        }

    def _synthetic_images(self) -> dict[str, Any]:
        return {
            "images": [
                {
                    "story_id": f"synthetic-story-{i}",
                    "image_id": f"synthetic-image-{i}",
                    "accepted": True,
                    "binary_digest": digest({"synthetic_image": i}),
                }
                for i in range(1, 7)
            ],
            "accepted_count": 6,
        }

    def _synthetic_watchlist(self) -> dict[str, Any]:
        return {
            "new_today": 0,
            "updated_today": 1,
            "carried_forward": 2,
            "topics": [{"topic_id": "synthetic-topic", "status": "updated"}],
        }

    def _rating_contract(self) -> dict[str, Any]:
        return {
            "contract_version": RATING_CONTRACT_VERSION,
            "scale": {"min": 1, "max": 5, "step": 1},
            "change_in_session": True,
            "aggregate": "arithmetic_mean_of_recorded_values",
            "privacy": "sender_rating_not_embedded_in_shared_copy",
            "missing_states": ["missing", "suppressed", "unavailable"],
            "legacy_policy": "preserve_original_contract_version_no_silent_conversion",
        }

    def _publication_bundle(self) -> dict[str, Any]:
        inputs = {}
        for name in ("edition", "media", "images", "watchlist", "rating-contract"):
            record = self.store.load_artifact(name)
            inputs[name] = record["content_digest"]
        return {
            "bundle_contract_version": "1.0.0",
            "ordered_input_digests": inputs,
            "synthetic": True,
        }

    def _maybe_inject(self, stage: str) -> None:
        if (
            self.failure_injection
            and not self._injection_fired
            and self.failure_injection.stage == stage
        ):
            self._injection_fired = True
            raise SyntheticFailure(self.failure_injection.failure_class)

    def _record_failure(self, run: dict[str, Any], failed_stage: str, exc: Exception) -> None:
        prior = run["current_state"]
        if prior != "Recovering":
            self.transition(run, "Recovering")
        run["recovery_target"] = failed_stage
        run["incident_count"] += 1
        retained = []
        for artifact_type in ("edition", "media", "images", "watchlist", "rating-contract"):
            artifact = self.store.load_artifact(artifact_type)
            if artifact and artifact.get("status") == "locked":
                retained.append(artifact_type)
        incident = {
            "schema_version": SCHEMA_VERSION,
            "incident_id": f"{self.run_id}:incident:{run['incident_count']}",
            "run_id": self.run_id,
            "edition_date": self.edition_date,
            "failed_stage": failed_stage,
            "failure_class": str(exc),
            "retained_locks": retained,
            "invalidated_artifacts": [],
            "repair_action": "resume_failed_boundary",
            "attempt": run["incident_count"] + 1,
            "result": "pending_recovery",
            "created_at": utc_now(),
        }
        self.store.write_incident(incident)
        self.store.write_run(run)

    def _recover_if_needed(self, run: dict[str, Any]) -> None:
        if run["current_state"] != "Recovering":
            return
        target = run.get("recovery_target")
        if not target:
            raise ContractError("Recovering state missing recovery_target")
        self.transition(run, target)
        incident = self.store.load_incident()
        if incident:
            incident["recovery_receipt"] = {
                "incident_id": incident["incident_id"],
                "failed_stage": incident["failed_stage"],
                "failure_class": incident["failure_class"],
                "retained_locks": incident["retained_locks"],
                "invalidated_artifacts": incident["invalidated_artifacts"],
                "repair_action": incident["repair_action"],
                "attempt": incident["attempt"],
                "result": "recovered",
                "recovered_at": utc_now(),
            }
            incident["result"] = "recovered"
            self.store.write_incident(incident)
        run["recovery_target"] = None
        self.store.write_run(run)

    def _book_evaluation(self) -> dict[str, Any]:
        bundle = self.store.load_artifact("publication-bundle")
        return {
            "evaluated_item_types": ["article", "video", "podcast"],
            "all_included_items_evaluated": True,
            "proposal_count": 0,
            "result": "0 proposals — all included items evaluated; no material book change warranted",
            "final_production_identity": f"synthetic-prod:{bundle['content_digest']}",
        }

    def _projection_watermark(self) -> dict[str, Any]:
        bundle = self.store.load_artifact("publication-bundle")
        evaluation = self.store.load_artifact("book-change-evaluation")
        return {
            "projection_schema_version": PROJECTION_SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "run_id": self.run_id,
            "canonical_record_digest": bundle["content_digest"],
            "final_production_identity": f"synthetic-prod:{bundle['content_digest']}",
            "completion_event_id": f"{self.run_id}:completion",
            "book_change_evaluation_digest": evaluation["content_digest"],
            "synced_at": utc_now(),
        }

    def _completion(self, run: dict[str, Any]) -> dict[str, Any]:
        bundle = self.store.load_artifact("publication-bundle")
        evaluation = self.store.load_artifact("book-change-evaluation")
        watermark = self.store.load_artifact("projection-watermark")
        receipts = {
            "publication_bundle_digest": bundle["content_digest"] if bundle else None,
            "deployment_identity": run["stage_receipts"].get("deployment_identity"),
            "live_verification": run["stage_receipts"].get("live_verification"),
            "book_change_evaluation_digest": evaluation["content_digest"] if evaluation else None,
            "projection_watermark_digest": watermark["content_digest"] if watermark else None,
        }
        missing = [name for name in MANDATORY_COMPLETION_RECEIPTS if not receipts.get(name)]
        if missing:
            raise IncompleteCompletion(f"missing mandatory receipts: {', '.join(missing)}")
        return {
            "completion_event_id": f"{self.run_id}:completion",
            "edition_date": self.edition_date,
            "run_id": self.run_id,
            "final_production_identity": watermark["data"]["final_production_identity"],
            "publication_bundle_digest": bundle["content_digest"],
            "deployment_identity": receipts["deployment_identity"],
            "live_verification_timestamp": receipts["live_verification"]["verified_at"],
            "book_change_evaluation_status": "complete",
            "command_center_watermark": watermark["content_digest"],
            "incident_count": run["incident_count"],
            "manual_intervention": run["manual_intervention"],
            "anti_rework": deepcopy(run["anti_rework"]),
            "overall_state": "Complete",
        }

    def run(self) -> dict[str, Any]:
        run = self.load_or_create()
        if run["current_state"] == "Complete":
            return run
        self.store.acquire_lease(self.run_id, self.owner)
        try:
            self._recover_if_needed(run)
            while run["current_state"] != "Complete":
                state = run["current_state"]
                try:
                    if state == "Ready":
                        self.transition(run, "Acquiring")
                    elif state == "Acquiring":
                        self._ensure_artifact(run, "edition", "acquiring", self._synthetic_edition)
                        self.transition(run, "Deciding")
                    elif state == "Deciding":
                        self._ensure_artifact(run, "rating-contract", "deciding", self._rating_contract)
                        self.transition(run, "Building")
                    elif state == "Building":
                        self._ensure_artifact(run, "media", "building:media", self._synthetic_media)
                        self._ensure_artifact(run, "images", "building:images", self._synthetic_images)
                        self._ensure_artifact(run, "watchlist", "building:watchlist", self._synthetic_watchlist)
                        self.transition(run, "Validating")
                    elif state == "Validating":
                        self._maybe_inject("Validating")
                        self._ensure_artifact(run, "publication-bundle", "validating", self._publication_bundle)
                        self.transition(run, "Releasing")
                    elif state == "Releasing":
                        bundle = self.store.load_artifact("publication-bundle")
                        self._count_stage(run, "releasing")
                        run["stage_receipts"]["release"] = {
                            "bundle_digest": bundle["content_digest"],
                            "released_at": utc_now(),
                        }
                        run["stage_receipts"]["deployment_identity"] = (
                            f"synthetic-deploy:{bundle['content_digest']}"
                        )
                        self.store.write_run(run)
                        self.transition(run, "Deployed")
                    elif state == "Deployed":
                        self._count_stage(run, "deployed")
                        run["stage_receipts"]["live_verification"] = {
                            "bundle_digest": self.store.load_artifact("publication-bundle")["content_digest"],
                            "verified_at": utc_now(),
                            "result": "passed",
                        }
                        self.store.write_run(run)
                        self.transition(run, "LiveVerified")
                    elif state == "LiveVerified":
                        self.transition(run, "PostPublicationEvaluation")
                    elif state == "PostPublicationEvaluation":
                        self._ensure_artifact(
                            run,
                            "book-change-evaluation",
                            "post_publication_evaluation",
                            self._book_evaluation,
                        )
                        self.transition(run, "OperationsReconciled")
                    elif state == "OperationsReconciled":
                        self._ensure_artifact(
                            run,
                            "projection-watermark",
                            "operations_reconciled:projection",
                            self._projection_watermark,
                        )
                        self._ensure_artifact(
                            run,
                            "completion",
                            "operations_reconciled:completion",
                            lambda: self._completion(run),
                        )
                        run["completion_status"] = "complete"
                        self.store.write_run(run)
                        self.transition(run, "Complete")
                    elif state == "Recovering":
                        self._recover_if_needed(run)
                    else:
                        raise ContractError(f"unhandled state: {state}")
                except SyntheticFailure as exc:
                    self._record_failure(run, state, exc)
                    raise
            return run
        finally:
            self.store.release_lease(self.owner)



def projection_freshness(watermark: dict[str, Any] | None, final_production_identity: str) -> dict[str, str]:
    """Deterministically classify Command Center projection freshness."""
    if not watermark:
        return {"status": "degraded", "reason": "watermark_missing"}
    represented = watermark.get("data", watermark).get("final_production_identity")
    if represented != final_production_identity:
        return {"status": "degraded", "reason": "final_production_identity_mismatch"}
    return {"status": "current", "reason": "identity_match"}

def start_daily_brief(
    edition_date: str,
    mode: str = "synthetic",
    state_root: Path | str = ".state",
    owner: str = "orchestrator",
    failure_injection: FailureInjection | None = None,
) -> dict[str, Any]:
    """Canonical manual/future-schedule entry point."""
    return RunEngine(state_root, edition_date, mode, owner, failure_injection).run()


def scheduled_start(
    edition_date: str,
    mode: str = "production",
    state_root: Path | str = ".state",
    owner: str = "scheduled-orchestrator",
) -> dict[str, Any]:
    """Future schedule adapter. Intentionally delegates to the exact same entry point."""
    return start_daily_brief(edition_date, mode, state_root, owner)
