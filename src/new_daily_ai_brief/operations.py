from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import ARTIFACT_DEPENDENCIES, PROJECTION_SCHEMA_VERSION, RATING_CONTRACT_VERSION, SCHEMA_VERSION
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class OperationsReconciliationError(ContractError):
    pass


class OperationsBoundaryFailure(OperationsReconciliationError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"operations:{boundary_id}"


def projection_currentness(
    watermark: dict[str, Any] | None,
    projection: dict[str, Any] | None,
    receipt: dict[str, Any] | None,
) -> dict[str, str]:
    """Classify projection state by bound identities, never by wall-clock age."""
    if not watermark:
        return {"status": "incomplete", "reason": "watermark_missing"}
    if not projection:
        return {"status": "incomplete", "reason": "projection_missing"}
    if not receipt:
        return {"status": "incomplete", "reason": "shadow_receipt_missing"}
    data = watermark.get("data", watermark)
    if data.get("projection_payload_digest") != projection.get("content_digest"):
        return {"status": "mismatched", "reason": "projection_identity_mismatch"}
    if data.get("canonical_chain_digest") != projection.get("data", {}).get("canonical_chain_digest"):
        return {"status": "stale", "reason": "canonical_chain_identity_mismatch"}
    if data.get("shadow_projection_receipt_digest") != digest(receipt):
        return {"status": "mismatched", "reason": "shadow_receipt_identity_mismatch"}
    if receipt.get("output_digest") != digest(projection.get("data", {})):
        return {"status": "mismatched", "reason": "shadow_output_identity_mismatch"}
    return {"status": "current", "reason": "identity_match"}


class OperationsReconciliationPipeline:
    """Iteration 8 deterministic synthetic/shadow Command Center projection model."""

    PROJECTION_CONTRACT_VERSION = "1.0.0"
    ADAPTER_VERSION = "fixture-filesystem-shadow-v1"

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
    )

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_operations_boundary_failure",
        record_validation_metrics: bool = True,
    ):
        self.record_validation_metrics = record_validation_metrics
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("operations:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "iteration8-operations-state.json"
        self.metrics_path = self.store.run_dir / "iteration8-metrics.json"
        self.shadow_dir = self.store.run_dir / "iteration8-shadow-command-center"
        self.shadow_projection_path = self.shadow_dir / "projection.json"
        self.shadow_receipt_path = self.shadow_dir / "projection-receipt.json"

    def _fail(self, boundary_type: str, boundary_id: str, message: str) -> None:
        state = self._load_state()
        state["metrics"]["validation_failures"] += 1
        self._save_state(state)
        self._write_metrics(state)
        raise OperationsBoundaryFailure(boundary_type, boundary_id, message)

    def _contract(self) -> dict[str, Any]:
        if self.mode == "production" or self.fixture_root is None:
            raise OperationsReconciliationError(
                "production/private-live projection is intentionally fail-closed: "
                "no approved zero-incremental-cost production projection adapter is configured"
            )
        path = self.fixture_root / "projection-contract.json"
        if not path.exists():
            raise OperationsReconciliationError(f"missing Iteration 8 projection contract fixture: {path}")
        contract = json.loads(path.read_text(encoding="utf-8"))
        checks = {
            "schema": contract.get("schema_version") == SCHEMA_VERSION,
            "contract": contract.get("projection_contract_version") == self.PROJECTION_CONTRACT_VERSION,
            "adapter": contract.get("projection_adapter_version") == self.ADAPTER_VERSION,
            "shadow": contract.get("shadow_only") is True,
            "production": contract.get("production_authorized") is False,
            "target": contract.get("target") == "isolated_fixture_filesystem_shadow",
        }
        if not all(checks.values()):
            raise OperationsReconciliationError("unsupported or unsafe Iteration 8 projection contract")
        return contract

    def _load_state(self) -> dict[str, Any]:
        existing = self.store.read_json(self.state_path)
        if existing:
            if existing.get("schema_version") != SCHEMA_VERSION or existing.get("edition_date") != self.edition_date:
                raise OperationsReconciliationError("Iteration 8 operations state is stale or schema-incompatible")
            return existing
        return {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "attempts": {"shadow_projection": 0, "watermark": 0},
            "metrics": {
                "validation_checks": 0,
                "validation_failures": 0,
                "projection_build_attempts": 0,
                "projection_reuse": 0,
                "materialization_attempts": 0,
                "materialization_retries": 0,
                "materialization_cache_reuse": 0,
                "materialization_failures": 0,
                "watermark_attempts": 0,
                "watermark_reuse": 0,
                "watermark_failures": 0,
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
                    "unrelated_projection_rewrite": 0,
                    "full_pipeline_restart": 0,
                },
            },
        }

    def _save_state(self, state: dict[str, Any]) -> None:
        if not self.record_validation_metrics:
            return
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, state: dict[str, Any]) -> None:
        if not self.record_validation_metrics:
            return
        payload = {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "recorded_at": utc_now(),
            "operations_reconciliation": deepcopy(state["metrics"]),
        }
        self.store._atomic_write(self.metrics_path, payload)

    def _require_locked(self, artifact_type: str) -> dict[str, Any]:
        record = self.store.load_artifact(artifact_type)
        if not record:
            self._fail("operations_validation", artifact_type, f"locked {artifact_type} is missing")
        if record.get("status") != "locked":
            self._fail("operations_validation", artifact_type, f"{artifact_type} is not locked")
        if record.get("schema_version") != SCHEMA_VERSION:
            self._fail("operations_validation", artifact_type, f"{artifact_type} schema is incompatible")
        if record.get("edition_date") != self.edition_date:
            self._fail("operations_validation", artifact_type, f"{artifact_type} is stale or wrong-date")
        if record.get("content_digest") != semantic_digest(record):
            self._fail("operations_validation", artifact_type, f"{artifact_type} semantic digest mismatch")
        expected_inputs = []
        for dependency in ARTIFACT_DEPENDENCIES[artifact_type]:
            dep = self.store.load_artifact(dependency)
            if not dep or dep.get("status") != "locked":
                self._fail("operations_validation", artifact_type, f"dependency {dependency} is not locked")
            expected_inputs.append(dep["content_digest"])
        if sorted(record.get("input_digests", [])) != sorted(expected_inputs):
            self._fail("operations_validation", artifact_type, f"{artifact_type} dependency binding mismatch")
        return record

    def _records(self) -> dict[str, dict[str, Any]]:
        self._contract()
        records = {name: self._require_locked(name) for name in self.CANONICAL_CHAIN}
        state = self._load_state()
        state["metrics"]["validation_checks"] += len(self.CANONICAL_CHAIN)
        self._save_state(state)

        edition = records["edition"]["data"]
        stories = sorted(edition.get("stories", []), key=lambda x: int(x.get("presentation_position", 0)))
        story_ids = [x.get("story_id") for x in stories]
        counts = {}
        for story in stories:
            counts[story.get("category_id")] = counts.get(story.get("category_id"), 0) + 1
        if len(stories) != 6 or [x.get("presentation_position") for x in stories] != list(range(1, 7)):
            self._fail("projection_membership", "stories", "exactly six ordered stories are required")
        if len(counts) != 3 or sorted(counts.values()) != [2, 2, 2]:
            self._fail("projection_membership", "allocation", "exact 2/2/2 category allocation is required")
        if sum(bool(x.get("agent_skills")) for x in stories) != 1:
            self._fail("projection_membership", "agent-skills", "exactly one Agent Skills story is required")

        media = records["media"]["data"]
        videos, podcasts = media.get("videos", []), media.get("podcasts", [])
        if len(videos) != 2 or not all(x.get("verified") for x in videos):
            self._fail("projection_membership", "videos", "exactly two verified videos are required")
        if len(podcasts) != 2 or not all(x.get("verified") for x in podcasts):
            self._fail("projection_membership", "podcasts", "exactly two verified podcasts are required")

        watch = records["watchlist"]["data"]
        counts_watch = watch.get("counts", {})
        for key in ("new_today", "updated_today", "carried_forward"):
            if counts_watch.get(key) != len(watch.get(key, [])):
                self._fail("projection_membership", "watchlist", f"Watchlist {key} count mismatch")
        if watch.get("edition_date") != self.edition_date:
            self._fail("projection_membership", "watchlist", "Watchlist is not edition-current")

        bridges = records["book-bridges"]["data"].get("decisions", [])
        if len(bridges) != 6 or [x.get("story_id") for x in bridges] != story_ids:
            self._fail("projection_membership", "book-bridges", "six ordered bridge decisions are required")

        images = records["images"]["data"].get("images", [])
        if len(images) != 6 or [x.get("story_id") for x in images] != story_ids or not all(x.get("accepted") for x in images):
            self._fail("projection_membership", "images", "six accepted ordered image bindings are required")

        rating = records["rating-contract"]["data"]
        if rating.get("contract_version") != RATING_CONTRACT_VERSION:
            self._fail("projection_membership", "rating", "five-star-v1 rating contract is required")

        bundle = records["publication-bundle"]
        ordered_inputs = bundle["data"].get("ordered_input_digests", {})
        for name in ("edition", "media", "images", "watchlist", "book-bridges", "rating-contract"):
            if ordered_inputs.get(name) != records[name]["content_digest"]:
                self._fail("projection_binding", "publication-bundle", f"publication bundle no longer binds {name}")

        reader = records["reader-render"]
        manifest = records["route-manifest"]
        package = records["release-package"]
        deployment = records["shadow-deployment"]
        verification = records["live-verification"]
        evaluation = records["book-change-evaluation"]

        if reader["data"].get("publication_bundle_digest") != bundle["content_digest"]:
            self._fail("projection_binding", "reader-render", "reader render publication binding mismatch")
        if reader["data"].get("story_order") != story_ids:
            self._fail("projection_binding", "reader-render", "reader story order differs from locked edition")
        if reader["data"].get("media", {}).get("video_ids") != [x["media_id"] for x in videos]:
            self._fail("projection_binding", "reader-render", "reader video membership mismatch")
        if reader["data"].get("media", {}).get("podcast_ids") != [x["media_id"] for x in podcasts]:
            self._fail("projection_binding", "reader-render", "reader podcast membership mismatch")
        if reader["data"].get("watchlist_counts") != counts_watch:
            self._fail("projection_binding", "reader-render", "reader Watchlist state mismatch")
        if reader["data"].get("bridge_decisions") != bridges:
            self._fail("projection_binding", "reader-render", "reader bridge state mismatch")
        expected_images = [
            {"story_id": x["story_id"], "image_id": x["image_id"], "binary_digest": x["binary_digest"]}
            for x in images
        ]
        if reader["data"].get("image_bindings") != expected_images:
            self._fail("projection_binding", "reader-render", "reader image binding mismatch")

        if manifest["data"].get("reader_render_digest") != reader["content_digest"]:
            self._fail("projection_binding", "route-manifest", "route manifest reader binding mismatch")
        if manifest["data"].get("publication_bundle_digest") != bundle["content_digest"]:
            self._fail("projection_binding", "route-manifest", "route manifest publication binding mismatch")
        if package["data"].get("route_manifest_digest") != manifest["content_digest"]:
            self._fail("projection_binding", "release-package", "release package route binding mismatch")
        if deployment["data"].get("release_package_digest") != package["content_digest"]:
            self._fail("projection_binding", "shadow-deployment", "deployment release binding mismatch")

        v = verification["data"]
        verification_ok = (
            v.get("verification_scope") == "shadow_offline"
            and v.get("result") == "passed"
            and v.get("shadow_only") is True
            and v.get("production_authorized") is False
            and v.get("route_manifest_digest") == manifest["content_digest"]
            and v.get("release_package_digest") == package["content_digest"]
            and v.get("deployment_identity") == deployment["data"].get("deployment_identity")
            and bool(v.get("checks"))
            and all(v["checks"].values())
        )
        if not verification_ok:
            self._fail("projection_binding", "live-verification", "live verification is stale, corrupted, or non-passing")

        e = evaluation["data"]
        expected_item_ids = story_ids + [x["media_id"] for x in videos] + [x["media_id"] for x in podcasts]
        expected_item_types = ["article"] * 6 + ["video"] * 2 + ["podcast"] * 2
        if (
            e.get("all_items_evaluated") is not True
            or e.get("evaluated_item_ids") != expected_item_ids
            or e.get("evaluated_item_types") != expected_item_types
            or len(e.get("item_evaluations", [])) != 10
        ):
            self._fail("projection_binding", "book-change-evaluation", "exactly 10 explicit successful item evaluations are required")
        if [x.get("item_id") for x in e.get("item_evaluations", [])] != expected_item_ids:
            self._fail("projection_binding", "book-change-evaluation", "evaluation item identities are incomplete or reordered")
        if not all(x.get("disposition") in {"proposal_warranted", "no_material_proposal"} for x in e["item_evaluations"]):
            self._fail("projection_binding", "book-change-evaluation", "evaluation contains a non-success disposition")
        if e.get("proposal_count") != len(e.get("proposal_records", [])):
            self._fail("projection_binding", "book-change-evaluation", "proposal count differs from proposal records")
        if e.get("missing_evaluation_is_zero") is not False:
            self._fail("projection_binding", "book-change-evaluation", "missing evaluation must not be interpreted as zero")
        if e.get("proposal_count") == 0 and (
            e.get("proposal_records") != [] or e.get("result_semantics") != "true_zero"
        ):
            self._fail("projection_binding", "book-change-evaluation", "true-zero proposal semantics are ambiguous")
        bound = e.get("bound_release", {})
        expected_bound = {
            "publication_bundle_digest": bundle["content_digest"],
            "route_manifest_digest": manifest["content_digest"],
            "release_package_digest": package["content_digest"],
            "shadow_deployment_digest": deployment["content_digest"],
            "shadow_deployment_identity": deployment["data"]["deployment_identity"],
            "live_verification_digest": verification["content_digest"],
        }
        for key, value in expected_bound.items():
            if bound.get(key) != value:
                self._fail("projection_binding", "book-change-evaluation", f"evaluation release binding mismatch: {key}")

        return records

    def _projection_data(self, records: dict[str, dict[str, Any]]) -> dict[str, Any]:
        edition = records["edition"]["data"]
        stories = sorted(edition["stories"], key=lambda x: int(x["presentation_position"]))
        media = records["media"]["data"]
        watch = records["watchlist"]["data"]
        bridges = records["book-bridges"]["data"]["decisions"]
        images = records["images"]["data"]["images"]
        rating = records["rating-contract"]["data"]
        evaluation = records["book-change-evaluation"]["data"]

        bindings = {name: records[name]["content_digest"] for name in self.CANONICAL_CHAIN}
        canonical_chain_digest = digest({"edition_date": self.edition_date, "bindings": bindings})
        story_projection = [
            {
                "story_id": x["story_id"],
                "presentation_position": x["presentation_position"],
                "category_id": x["category_id"],
                "agent_skills": bool(x["agent_skills"]),
            }
            for x in stories
        ]
        projection = {
            "projection_contract_version": self.PROJECTION_CONTRACT_VERSION,
            "projection_adapter_version": self.ADAPTER_VERSION,
            "edition_date": self.edition_date,
            "run_id": f"dab-{self.edition_date}-{self.mode}",
            "bindings": bindings,
            "canonical_chain_digest": canonical_chain_digest,
            "stories": story_projection,
            "category_allocation": deepcopy(edition["category_counts"]),
            "agent_skills_count": 1,
            "media": {
                "videos": [{"media_id": x["media_id"], "verified": x["verified"]} for x in media["videos"]],
                "podcasts": [{"media_id": x["media_id"], "verified": x["verified"]} for x in media["podcasts"]],
            },
            "watchlist": {
                "counts": deepcopy(watch["counts"]),
                "new_today_ids": [x["topic_id"] for x in watch["new_today"]],
                "updated_today_ids": [x["topic_id"] for x in watch["updated_today"]],
                "carried_forward_ids": [x["topic_id"] for x in watch["carried_forward"]],
            },
            "book_bridges": deepcopy(bridges),
            "image_bindings": [
                {"story_id": x["story_id"], "image_id": x["image_id"], "binary_digest": x["binary_digest"]}
                for x in images
            ],
            "rating_contract": {
                "contract_version": rating["contract_version"],
                "scale": deepcopy(rating["scale"]),
                "change_in_session": rating["change_in_session"],
                "aggregate": rating["aggregate"],
                "privacy": rating["privacy"],
                "stored_rating_values": None,
                "fabricated_rating_values": False,
            },
            "release": {
                "publication_bundle_digest": records["publication-bundle"]["content_digest"],
                "reader_render_digest": records["reader-render"]["content_digest"],
                "route_manifest_digest": records["route-manifest"]["content_digest"],
                "release_package_digest": records["release-package"]["content_digest"],
                "shadow_deployment_digest": records["shadow-deployment"]["content_digest"],
                "shadow_deployment_identity": records["shadow-deployment"]["data"]["deployment_identity"],
                "live_verification_digest": records["live-verification"]["content_digest"],
                "verification_scope": records["live-verification"]["data"]["verification_scope"],
                "verification_result": records["live-verification"]["data"]["result"],
            },
            "book_change_evaluation": {
                "evaluation_digest": records["book-change-evaluation"]["content_digest"],
                "evaluated_item_ids": deepcopy(evaluation["evaluated_item_ids"]),
                "evaluated_item_types": deepcopy(evaluation["evaluated_item_types"]),
                "explicit_item_evaluation_count": len(evaluation["item_evaluations"]),
                "proposal_count": evaluation["proposal_count"],
                "proposal_record_ids": [x["proposal_id"] for x in evaluation["proposal_records"]],
                "result_semantics": evaluation["result_semantics"],
                "all_items_evaluated": evaluation["all_items_evaluated"],
                "missing_evaluation_is_zero": evaluation["missing_evaluation_is_zero"],
            },
            "missingness": {
                "proposal_state": evaluation["result_semantics"],
                "numeric_zero_is_distinct_from_missing": True,
                "unknown_unavailable_suppressed_are_distinct": True,
            },
            "operational_domains": {
                "editorial_discovery": deepcopy(records["discovery"]["data"]),
                "edition_content": deepcopy(edition),
                "media_content": deepcopy(media),
                "watchlist_content": deepcopy(watch),
                "image_content": {
                    "accepted_count": records["images"]["data"].get("accepted_count"),
                    "quality_contract": deepcopy(records["images"]["data"].get("quality_contract")),
                    "images": deepcopy(images),
                },
                "publication_infrastructure": {
                    "publication_bundle": deepcopy(records["publication-bundle"]["data"]),
                    "reader_render": deepcopy(records["reader-render"]["data"]),
                    "route_manifest": deepcopy(records["route-manifest"]["data"]),
                    "release_package": deepcopy(records["release-package"]["data"]),
                    "live_verification": deepcopy(records["live-verification"]["data"]),
                },
                "artifact_provenance": {
                    name: {
                        "content_digest": records[name]["content_digest"],
                        "schema_version": records[name]["schema_version"],
                        "produced_by_stage": records[name].get("produced_by_stage"),
                    }
                    for name in self.CANONICAL_CHAIN
                },
            },
            "bounded_lifecycle": {
                "state": "OperationsReconciled",
                "completion_status": "operations_reconciled_locked",
                "complete_transition_allowed_in_iteration8": False,
                "final_completion_artifact_allowed_in_iteration8": False,
            },
            "shadow_only": True,
            "production_authorized": False,
        }
        return projection

    def build_projection(self) -> dict[str, Any]:
        started = time.monotonic()
        records = self._records()
        state = self._load_state()
        state["metrics"]["projection_build_attempts"] += 1
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state(state)
        self._write_metrics(state)
        return self._projection_data(records)

    def _expected_shadow_receipt(self, projection: dict[str, Any]) -> dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "projection_contract_version": self.PROJECTION_CONTRACT_VERSION,
            "projection_adapter_version": self.ADAPTER_VERSION,
            "edition_date": self.edition_date,
            "target": "isolated_fixture_filesystem_shadow",
            "projection_artifact_digest": projection["content_digest"],
            "projection_payload_digest": digest(projection["data"]),
            "output_digest": digest(projection["data"]),
            "shadow_only": True,
            "production_authorized": False,
        }

    def _validate_shadow_output(self, projection: dict[str, Any]) -> dict[str, Any] | None:
        output = self.store.read_json(self.shadow_projection_path)
        receipt = self.store.read_json(self.shadow_receipt_path)
        if output is None and receipt is None:
            return None
        if output is None or receipt is None:
            self._fail("shadow_projection", "materialization", "shadow projection target is incomplete")
        if output != projection["data"]:
            self._fail("shadow_projection", "materialization", "shadow projection payload is corrupted or stale")
        expected = self._expected_shadow_receipt(projection)
        if receipt != expected:
            self._fail("shadow_projection", "materialization", "shadow projection receipt is corrupted or mismatched")
        return receipt

    def materialize_shadow_projection(self, projection: dict[str, Any]) -> dict[str, Any]:
        started = time.monotonic()
        self._contract()
        state = self._load_state()
        existing = self._validate_shadow_output(projection)
        if existing is not None:
            state["metrics"]["materialization_cache_reuse"] += 1
            state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._save_state(state)
            self._write_metrics(state)
            return existing

        state["attempts"]["shadow_projection"] += 1
        state["metrics"]["materialization_attempts"] += 1
        if state["attempts"]["shadow_projection"] > 1:
            state["metrics"]["materialization_retries"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "shadow_projection" and not self._failure_fired:
            self._failure_fired = True
            state["metrics"]["materialization_failures"] += 1
            self._save_state(state)
            self._write_metrics(state)
            raise OperationsBoundaryFailure("shadow_projection", "shadow_projection", self.failure_class)

        receipt = self._expected_shadow_receipt(projection)
        self.shadow_dir.mkdir(parents=True, exist_ok=True)
        self.store._atomic_write(self.shadow_projection_path, projection["data"])
        self.store._atomic_write(self.shadow_receipt_path, receipt)
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state(state)
        self._write_metrics(state)
        return receipt

    def _watermark_data(self, projection: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
        p = projection["data"]
        identity_core = {
            "projection_contract_version": self.PROJECTION_CONTRACT_VERSION,
            "canonical_chain_digest": p["canonical_chain_digest"],
            "projection_payload_digest": projection["content_digest"],
            "shadow_projection_receipt_digest": digest(receipt),
        }
        return {
            "projection_schema_version": PROJECTION_SCHEMA_VERSION,
            "projection_contract_version": self.PROJECTION_CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "run_id": p["run_id"],
            "canonical_chain_digest": p["canonical_chain_digest"],
            "projection_payload_digest": projection["content_digest"],
            "shadow_projection_receipt_digest": digest(receipt),
            "shadow_projection_output_digest": receipt["output_digest"],
            "bindings": deepcopy(p["bindings"]),
            "publication_bundle_digest": p["release"]["publication_bundle_digest"],
            "reader_render_digest": p["release"]["reader_render_digest"],
            "route_manifest_digest": p["release"]["route_manifest_digest"],
            "release_package_digest": p["release"]["release_package_digest"],
            "shadow_deployment_digest": p["release"]["shadow_deployment_digest"],
            "shadow_deployment_identity": p["release"]["shadow_deployment_identity"],
            "live_verification_digest": p["release"]["live_verification_digest"],
            "live_verification_scope": p["release"]["verification_scope"],
            "book_change_evaluation_digest": p["book_change_evaluation"]["evaluation_digest"],
            "reconciliation_identity": digest(identity_core),
            "currentness_semantics": "identity_bound_not_timestamp",
            "shadow_only": True,
            "production_authorized": False,
        }

    def build_watermark(self, projection: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
        state = self._load_state()
        state["attempts"]["watermark"] += 1
        state["metrics"]["watermark_attempts"] += 1
        self._save_state(state)
        if self.failure_boundary_id == "watermark" and not self._failure_fired:
            self._failure_fired = True
            state["metrics"]["watermark_failures"] += 1
            self._save_state(state)
            self._write_metrics(state)
            raise OperationsBoundaryFailure("projection_watermark", "watermark", self.failure_class)
        self._write_metrics(state)
        return self._watermark_data(projection, receipt)

    def validate_existing_projection_set(self) -> None:
        records = self._records()
        expected_projection = self._projection_data(records)
        projection = self.store.load_artifact("command-center-projection")
        watermark = self.store.load_artifact("projection-watermark")

        if projection is None:
            if watermark or self.shadow_projection_path.exists() or self.shadow_receipt_path.exists():
                self._fail("projection_validation", "projection", "downstream projection state exists without projection payload")
            return

        projection = self._require_locked("command-center-projection")
        if projection.get("data") != expected_projection:
            self._fail("projection_validation", "projection", "cached projection payload is stale or corrupted")
        state = self._load_state()
        state["metrics"]["projection_reuse"] += 1
        self._save_state(state)

        receipt = self._validate_shadow_output(projection)
        if watermark is not None:
            if receipt is None:
                self._fail("projection_validation", "watermark", "projection watermark exists without durable shadow projection")
            watermark = self._require_locked("projection-watermark")
            expected_watermark = self._watermark_data(projection, receipt)
            if watermark.get("data") != expected_watermark:
                self._fail("projection_validation", "watermark", "projection watermark is stale, corrupted, or mismatched")
            if projection_currentness(watermark, projection, receipt)["status"] != "current":
                self._fail("projection_validation", "currentness", "projection identity is not current")
            state = self._load_state()
            state["metrics"]["watermark_reuse"] += 1
            self._save_state(state)
        self._write_metrics(self._load_state())

    def validate_complete_reconciliation(
        self,
        projection: dict[str, Any],
        receipt: dict[str, Any],
        watermark: dict[str, Any],
    ) -> None:
        projection = self._require_locked("command-center-projection")
        watermark = self._require_locked("projection-watermark")
        if self._validate_shadow_output(projection) != receipt:
            self._fail("projection_validation", "shadow_projection", "shadow projection receipt changed during reconciliation")
        if watermark.get("data") != self._watermark_data(projection, receipt):
            self._fail("projection_validation", "watermark", "locked projection watermark does not bind current projection")
        currentness = projection_currentness(watermark, projection, receipt)
        if currentness["status"] != "current":
            self._fail("projection_validation", "currentness", currentness["reason"])
        self._write_metrics(self._load_state())
