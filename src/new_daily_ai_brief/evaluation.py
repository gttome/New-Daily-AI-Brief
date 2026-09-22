from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import ARTIFACT_DEPENDENCIES, SCHEMA_VERSION
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class PostPublicationEvaluationError(ContractError):
    pass


class EvaluationBoundaryFailure(PostPublicationEvaluationError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"evaluation:{boundary_id}"


class PostPublicationEvaluationPipeline:
    """Deterministic Iteration 7 post-publication Professional Series evaluation."""

    EVALUATION_CONTRACT_VERSION = "1.0.0"
    EVALUATOR_ADAPTER_VERSION = "fixture-book-change-v1"
    VERIFICATION_SCOPE = "shadow_offline"
    ALLOWED_DISPOSITIONS = {
        "proposal_warranted",
        "no_material_proposal",
        "unavailable_invalid_input",
        "not_evaluated",
    }

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_evaluation_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("evaluation:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "post-publication-evaluation-state.json"
        self.metrics_path = self.store.run_dir / "iteration7-metrics.json"

    def _fail(self, boundary_type: str, boundary_id: str, message: str) -> None:
        raise EvaluationBoundaryFailure(boundary_type, boundary_id, message)

    def _contract(self) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise PostPublicationEvaluationError(
                "production post-publication evaluation is intentionally fail-closed: "
                "no approved zero-incremental-cost production evaluator is configured"
            )
        path = self.fixture_root / "evaluation-contract.json"
        if not path.exists():
            raise PostPublicationEvaluationError(f"missing Iteration 7 evaluation contract fixture: {path}")
        contract = json.loads(path.read_text(encoding="utf-8"))
        checks = {
            "schema_version": contract.get("schema_version") == SCHEMA_VERSION,
            "evaluation_contract_version": contract.get("evaluation_contract_version")
            == self.EVALUATION_CONTRACT_VERSION,
            "adapter_version": contract.get("evaluator_adapter_version")
            == self.EVALUATOR_ADAPTER_VERSION,
            "article_count": contract.get("required_counts", {}).get("article") == 6,
            "video_count": contract.get("required_counts", {}).get("video") == 2,
            "podcast_count": contract.get("required_counts", {}).get("podcast") == 2,
            "proposal_types_valid": set(contract.get("proposal_item_types", []))
            <= {"article", "video", "podcast"},
            "shadow_only": contract.get("shadow_only") is True,
            "production_authorized": contract.get("production_authorized") is False,
        }
        if not all(checks.values()):
            raise PostPublicationEvaluationError("unsupported or unsafe Iteration 7 evaluation contract")
        return contract

    def _require_locked(self, artifact_type: str) -> dict[str, Any]:
        record = self.store.load_artifact(artifact_type)
        if not record:
            self._fail("evaluation_validation", artifact_type, f"locked {artifact_type} is missing")
        if record.get("status") != "locked":
            self._fail("evaluation_validation", artifact_type, f"{artifact_type} is not locked")
        if record.get("schema_version") != SCHEMA_VERSION:
            self._fail("evaluation_validation", artifact_type, f"{artifact_type} schema is incompatible")
        if record.get("edition_date") != self.edition_date:
            self._fail("evaluation_validation", artifact_type, f"{artifact_type} is stale or wrong-date")
        if record.get("content_digest") != semantic_digest(record):
            self._fail("evaluation_validation", artifact_type, f"{artifact_type} semantic digest mismatch")
        expected_inputs = []
        for dependency in ARTIFACT_DEPENDENCIES[artifact_type]:
            dep = self.store.load_artifact(dependency)
            if not dep or dep.get("status") != "locked":
                self._fail(
                    "evaluation_validation",
                    artifact_type,
                    f"dependency {dependency} is not locked",
                )
            expected_inputs.append(dep["content_digest"])
        if sorted(record.get("input_digests", [])) != sorted(expected_inputs):
            self._fail(
                "evaluation_validation",
                artifact_type,
                f"{artifact_type} input digests do not match locked dependencies",
            )
        return record

    def _required_inputs(self) -> tuple[dict[str, Any], dict[str, dict[str, Any]], list[dict[str, Any]]]:
        contract = self._contract()
        records = {
            name: self._require_locked(name)
            for name in (
                "edition",
                "media",
                "publication-bundle",
                "reader-render",
                "route-manifest",
                "release-package",
                "shadow-deployment",
                "live-verification",
            )
        }
        edition = records["edition"]
        media = records["media"]
        bundle = records["publication-bundle"]
        reader = records["reader-render"]
        manifest = records["route-manifest"]
        package = records["release-package"]
        deployment = records["shadow-deployment"]
        verification = records["live-verification"]

        ordered_inputs = bundle.get("data", {}).get("ordered_input_digests", {})
        if ordered_inputs.get("edition") != edition["content_digest"]:
            self._fail("evaluation_validation", "publication-bundle", "edition no longer matches publication bundle")
        if ordered_inputs.get("media") != media["content_digest"]:
            self._fail("evaluation_validation", "publication-bundle", "media no longer matches publication bundle")
        if reader.get("input_digests") != [bundle["content_digest"]]:
            self._fail("evaluation_validation", "reader-render", "reader-render bundle binding mismatch")
        if manifest.get("input_digests") != [reader["content_digest"]]:
            self._fail("evaluation_validation", "route-manifest", "route-manifest reader binding mismatch")
        if package.get("input_digests") != [manifest["content_digest"]]:
            self._fail("evaluation_validation", "release-package", "release-package manifest binding mismatch")
        if deployment.get("input_digests") != [package["content_digest"]]:
            self._fail("evaluation_validation", "shadow-deployment", "deployment package binding mismatch")
        if verification.get("input_digests") != [deployment["content_digest"]]:
            self._fail("evaluation_validation", "live-verification", "verification deployment binding mismatch")

        if reader["data"].get("publication_bundle_digest") != bundle["content_digest"]:
            self._fail("evaluation_validation", "reader-render", "reader-render publication digest mismatch")
        if manifest["data"].get("reader_render_digest") != reader["content_digest"]:
            self._fail("evaluation_validation", "route-manifest", "route-manifest reader digest mismatch")
        if manifest["data"].get("publication_bundle_digest") != bundle["content_digest"]:
            self._fail("evaluation_validation", "route-manifest", "route-manifest publication digest mismatch")
        if package["data"].get("route_manifest_digest") != manifest["content_digest"]:
            self._fail("evaluation_validation", "release-package", "release-package manifest digest mismatch")
        if deployment["data"].get("release_package_digest") != package["content_digest"]:
            self._fail("evaluation_validation", "shadow-deployment", "deployment release digest mismatch")

        v = verification["data"]
        verification_checks = {
            "scope": v.get("verification_scope") == self.VERIFICATION_SCOPE,
            "result": v.get("result") == "passed",
            "shadow_only": v.get("shadow_only") is True,
            "production_authorized": v.get("production_authorized") is False,
            "route_manifest": v.get("route_manifest_digest") == manifest["content_digest"],
            "release_package": v.get("release_package_digest") == package["content_digest"],
            "deployment_identity": v.get("deployment_identity")
            == deployment["data"].get("deployment_identity"),
            "checks": bool(v.get("checks")) and all(v["checks"].values()),
        }
        if not all(verification_checks.values()):
            self._fail(
                "evaluation_validation",
                "live-verification",
                "live verification is stale, corrupted, incomplete, or unsafe",
            )
        if deployment["data"].get("shadow_only") is not True:
            self._fail("evaluation_validation", "shadow-deployment", "deployment is not shadow-only")
        if deployment["data"].get("production_authorized") is not False:
            self._fail("evaluation_validation", "shadow-deployment", "production deployment is not authorized")

        stories = sorted(
            edition["data"].get("stories", []),
            key=lambda item: int(item.get("presentation_position", 0)),
        )
        videos = media["data"].get("videos", [])
        podcasts = media["data"].get("podcasts", [])
        if len(stories) != 6 or [x.get("presentation_position") for x in stories] != list(range(1, 7)):
            self._fail("evaluation_membership", "articles", "exactly six ordered stories are required")
        if len(videos) != 2 or not all(x.get("verified") for x in videos):
            self._fail("evaluation_membership", "videos", "exactly two verified videos are required")
        if len(podcasts) != 2 or not all(x.get("verified") for x in podcasts):
            self._fail("evaluation_membership", "podcasts", "exactly two verified podcasts are required")

        story_ids = [x.get("story_id") for x in stories]
        video_ids = [x.get("media_id") for x in videos]
        podcast_ids = [x.get("media_id") for x in podcasts]
        reader_data = reader["data"]
        if reader_data.get("story_order") != story_ids:
            self._fail("evaluation_membership", "articles", "reader story order differs from locked edition")
        if reader_data.get("media", {}).get("video_ids") != video_ids:
            self._fail("evaluation_membership", "videos", "reader video membership differs from locked media")
        if reader_data.get("media", {}).get("podcast_ids") != podcast_ids:
            self._fail("evaluation_membership", "podcasts", "reader podcast membership differs from locked media")

        items: list[dict[str, Any]] = []
        for index, story in enumerate(stories, start=1):
            items.append(
                {
                    "item_id": story["story_id"],
                    "item_type": "article",
                    "included_order": index,
                    "title": story.get("headline") or story.get("title") or story["story_id"],
                    "source_identity_digest": digest(story),
                }
            )
        for offset, item in enumerate(videos, start=7):
            items.append(
                {
                    "item_id": item["media_id"],
                    "item_type": "video",
                    "included_order": offset,
                    "title": item["title"],
                    "source_identity_digest": digest(item),
                }
            )
        for offset, item in enumerate(podcasts, start=9):
            items.append(
                {
                    "item_id": item["media_id"],
                    "item_type": "podcast",
                    "included_order": offset,
                    "title": item["title"],
                    "source_identity_digest": digest(item),
                }
            )
        ids = [x["item_id"] for x in items]
        if len(items) != 10 or len(set(ids)) != 10:
            self._fail("evaluation_membership", "items", "evaluation membership must contain exactly ten unique items")
        if [x["item_type"] for x in items] != ["article"] * 6 + ["video"] * 2 + ["podcast"] * 2:
            self._fail("evaluation_membership", "items", "evaluation membership must be 6 articles, 2 videos, 2 podcasts")

        return contract, records, items

    def _binding(self, contract: dict[str, Any], records: dict[str, dict[str, Any]]) -> dict[str, Any]:
        return {
            "evaluation_contract_version": contract["evaluation_contract_version"],
            "publication_bundle_digest": records["publication-bundle"]["content_digest"],
            "route_manifest_digest": records["route-manifest"]["content_digest"],
            "release_package_digest": records["release-package"]["content_digest"],
            "shadow_deployment_digest": records["shadow-deployment"]["content_digest"],
            "shadow_deployment_identity": records["shadow-deployment"]["data"]["deployment_identity"],
            "live_verification_digest": records["live-verification"]["content_digest"],
        }

    def _load_state(self, binding: dict[str, Any], contract_digest: str) -> dict[str, Any]:
        state = self.store.read_json(self.state_path)
        if state:
            if state.get("schema_version") != SCHEMA_VERSION:
                self._fail("evaluation_state", "state", "evaluation state schema is incompatible")
            if state.get("edition_date") != self.edition_date:
                self._fail("evaluation_state", "state", "evaluation state is stale")
            if state.get("contract_digest") != contract_digest:
                self._fail("evaluation_state", "state", "evaluation state binds a different contract")
            if state.get("bound_release") != binding:
                self._fail("evaluation_state", "state", "evaluation state binds a different release chain")
            return state
        return {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "contract_digest": contract_digest,
            "bound_release": binding,
            "attempts": {},
            "evaluations": {},
            "metrics": {
                "item_attempts": 0,
                "item_retries": 0,
                "item_cache_reuse": 0,
                "item_failures": 0,
                "item_completions": 0,
                "unrelated_item_rewrites": 0,
                "artifact_attempts": 0,
                "artifact_reuse": 0,
                "artifact_failures": 0,
                "validation_checks": 0,
                "validation_failures": 0,
                "elapsed_ms": 0,
            },
        }

    def _write_metrics(self, state: dict[str, Any]) -> None:
        payload = {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "recorded_at": utc_now(),
            "item_evaluation": deepcopy(state["metrics"]),
        }
        self.store._atomic_write(self.metrics_path, payload)

    def _decision(
        self,
        contract: dict[str, Any],
        binding: dict[str, Any],
        item: dict[str, Any],
    ) -> dict[str, Any]:
        warranted = item["item_type"] in set(contract.get("proposal_item_types", []))
        disposition = "proposal_warranted" if warranted else "no_material_proposal"
        evidence_id = digest(
            {
                "adapter": self.EVALUATOR_ADAPTER_VERSION,
                "contract_digest": digest(contract),
                "bound_release": binding,
                "item": item,
            }
        )
        if warranted:
            rationale = (
                f"Synthetic fixture marks {item['item_type']} items for deterministic "
                "Generative AI Professional Series change review."
            )
        else:
            rationale = (
                "Synthetic fixture found no material Generative AI Professional Series "
                "change warranted for this included item."
            )
        return {
            "evaluation_contract_version": self.EVALUATION_CONTRACT_VERSION,
            "item_id": item["item_id"],
            "item_type": item["item_type"],
            "included_order": item["included_order"],
            "source_identity_digest": item["source_identity_digest"],
            "disposition": disposition,
            "proposal_warranted": warranted,
            "rationale": rationale,
            "evidence_id": evidence_id,
        }

    def _validate_cached_decision(self, item: dict[str, Any], cached: dict[str, Any]) -> dict[str, Any]:
        data = cached.get("data")
        if not isinstance(data, dict):
            self._fail("item_evaluation", item["item_id"], "cached item evaluation data is missing")
        if cached.get("content_digest") != digest(data):
            self._fail("item_evaluation", item["item_id"], "cached item evaluation is corrupted")
        checks = {
            "id": data.get("item_id") == item["item_id"],
            "type": data.get("item_type") == item["item_type"],
            "order": data.get("included_order") == item["included_order"],
            "source": data.get("source_identity_digest") == item["source_identity_digest"],
            "disposition": data.get("disposition") in self.ALLOWED_DISPOSITIONS,
            "proposal_flag": data.get("proposal_warranted")
            == (data.get("disposition") == "proposal_warranted"),
        }
        if not all(checks.values()):
            self._fail("item_evaluation", item["item_id"], "cached item evaluation is incomplete or inconsistent")
        return data

    def _proposal(self, decision: dict[str, Any]) -> dict[str, Any]:
        core = {
            "item_id": decision["item_id"],
            "item_type": decision["item_type"],
            "action": "review_for_professional_series_update",
            "target": "Generative AI Professional Series",
            "rationale": decision["rationale"],
            "evidence_id": decision["evidence_id"],
        }
        return {
            "proposal_id": "book-change:" + digest(core).removeprefix("sha256:"),
            **core,
        }

    def _artifact_from_state(
        self,
        contract: dict[str, Any],
        binding: dict[str, Any],
        items: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        decisions = []
        for item in items:
            cached = state.get("evaluations", {}).get(item["item_id"])
            if not cached:
                self._fail("evaluation_artifact", item["item_id"], "included item is not evaluated")
            decisions.append(self._validate_cached_decision(item, cached))

        dispositions = [x["disposition"] for x in decisions]
        all_items_evaluated = len(decisions) == 10 and all(
            value in {"proposal_warranted", "no_material_proposal"} for value in dispositions
        )
        if not all_items_evaluated:
            self._fail(
                "evaluation_artifact",
                "completeness",
                "all ten included items must be explicitly and successfully evaluated",
            )
        proposals = [self._proposal(item) for item in decisions if item["proposal_warranted"]]
        proposal_count = len(proposals)
        if proposal_count == 0:
            result = "0 proposals — all 10 included items evaluated; no material book change warranted"
            result_semantics = "true_zero"
        else:
            result = (
                f"{proposal_count} proposals — all 10 included items evaluated; "
                "proposal records are explicitly persisted"
            )
            result_semantics = "proposals_present"
        if proposal_count != sum(x["disposition"] == "proposal_warranted" for x in decisions):
            self._fail("evaluation_artifact", "proposal-count", "proposal count differs from item dispositions")

        return {
            "evaluation_contract_version": self.EVALUATION_CONTRACT_VERSION,
            "evaluator_adapter_version": self.EVALUATOR_ADAPTER_VERSION,
            "edition_date": self.edition_date,
            "bound_release": binding,
            "evaluated_item_ids": [x["item_id"] for x in decisions],
            "evaluated_item_types": [x["item_type"] for x in decisions],
            "item_evaluations": decisions,
            "all_items_evaluated": True,
            "proposal_records": proposals,
            "proposal_count": proposal_count,
            "result": result,
            "result_semantics": result_semantics,
            "missing_evaluation_is_zero": False,
            "shadow_only": contract["shadow_only"],
            "production_authorized": contract["production_authorized"],
        }

    def validate_release_chain(self) -> None:
        self._required_inputs()

    def validate_existing_evaluation_set(self) -> None:
        contract, records, items = self._required_inputs()
        binding = self._binding(contract, records)
        contract_digest = digest(contract)
        state = self.store.read_json(self.state_path)
        artifact = self.store.load_artifact("book-change-evaluation")
        if not state and not artifact:
            return
        if not state:
            self._fail("evaluation_state", "state", "evaluation artifact exists without durable item state")
        state = self._load_state(binding, contract_digest)
        for item in items:
            cached = state.get("evaluations", {}).get(item["item_id"])
            if cached:
                self._validate_cached_decision(item, cached)
        if artifact:
            artifact = self._require_locked("book-change-evaluation")
            expected = self._artifact_from_state(contract, binding, items, state)
            if artifact.get("data") != expected:
                self._fail("evaluation_artifact", "artifact", "locked evaluation artifact is stale or corrupted")
            state["metrics"]["artifact_reuse"] += 1
            self.store._atomic_write(self.state_path, state)
            self._write_metrics(state)

    def build_evaluation(self) -> dict[str, Any]:
        started = time.monotonic()
        contract, records, items = self._required_inputs()
        binding = self._binding(contract, records)
        contract_digest = digest(contract)
        state = self._load_state(binding, contract_digest)
        baseline_evaluations = deepcopy(state.get("evaluations", {}))
        state["metrics"]["validation_checks"] += 12

        for item in items:
            item_id = item["item_id"]
            cached = state["evaluations"].get(item_id)
            if cached:
                self._validate_cached_decision(item, cached)
                state["metrics"]["item_cache_reuse"] += 1
                self.store._atomic_write(self.state_path, state)
                continue

            attempt = int(state["attempts"].get(item_id, 0)) + 1
            state["attempts"][item_id] = attempt
            state["metrics"]["item_attempts"] += 1
            if attempt > 1:
                state["metrics"]["item_retries"] += 1
            self.store._atomic_write(self.state_path, state)

            if self.failure_boundary_id == f"item:{item_id}" and not self._failure_fired:
                self._failure_fired = True
                state["metrics"]["item_failures"] += 1
                state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
                self.store._atomic_write(self.state_path, state)
                self._write_metrics(state)
                raise EvaluationBoundaryFailure("item_evaluation", f"item:{item_id}", self.failure_class)

            decision = self._decision(contract, binding, item)
            state["evaluations"][item_id] = {
                "content_digest": digest(decision),
                "data": decision,
            }
            state["metrics"]["item_completions"] += 1
            self.store._atomic_write(self.state_path, state)

        for item_id, previous in baseline_evaluations.items():
            if state["evaluations"].get(item_id) != previous:
                state["metrics"]["unrelated_item_rewrites"] += 1

        state["metrics"]["artifact_attempts"] += 1
        self.store._atomic_write(self.state_path, state)
        if self.failure_boundary_id == "artifact" and not self._failure_fired:
            self._failure_fired = True
            state["metrics"]["artifact_failures"] += 1
            state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self.store._atomic_write(self.state_path, state)
            self._write_metrics(state)
            raise EvaluationBoundaryFailure("evaluation_artifact", "artifact", self.failure_class)

        artifact = self._artifact_from_state(contract, binding, items, state)
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self.store._atomic_write(self.state_path, state)
        self._write_metrics(state)
        return artifact
