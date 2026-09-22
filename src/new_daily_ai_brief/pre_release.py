from __future__ import annotations

import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import ARTIFACT_DEPENDENCIES, RATING_CONTRACT_VERSION, SCHEMA_VERSION
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class PreReleaseError(ContractError):
    pass


class ImageBoundaryFailure(PreReleaseError):
    def __init__(self, story_id: str, failure_class: str):
        super().__init__(failure_class)
        self.story_id = story_id
        self.candidate_id = f"image:{story_id}"
        self.boundary_type = "image"
        self.boundary_id = story_id
        self.failure_class = failure_class


class ValidationBoundaryFailure(PreReleaseError):
    def __init__(self, invariant: str, message: str):
        super().__init__(f"{invariant}: {message}")
        self.boundary_type = "validation"
        self.boundary_id = invariant
        self.invariant = invariant


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


class PreReleasePipeline:
    IMAGE_CONTRACT_VERSION = "1.0.0"
    BUNDLE_CONTRACT_VERSION = "1.0.0"
    REQUIRED_BUNDLE_INPUTS = (
        "edition",
        "media",
        "images",
        "watchlist",
        "book-bridges",
        "rating-contract",
    )
    EXPECTED_CATEGORIES = {
        "agents_non_technical_people": 2,
        "applied_genai_knowledge_workers": 2,
        "technical_ai_engineering": 2,
    }

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_image_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = failure_boundary_id
        self.failure_class = failure_class
        self._failure_fired = False
        self.image_state_path = self.store.run_dir / "image-state.json"
        self.metrics_path = self.store.run_dir / "iteration4-metrics.json"

    def _catalog(self) -> dict[str, Any]:
        if self.fixture_root is None:
            raise PreReleaseError(
                "production image generation is intentionally fail-closed: "
                "no approved zero-incremental-cost autonomous image adapter is configured"
            )
        path = self.fixture_root / "image-catalog.json"
        if not path.exists():
            raise PreReleaseError(f"missing Iteration 4 image fixture: {path}")
        catalog = _read(path)
        if catalog.get("schema_version") != SCHEMA_VERSION:
            raise PreReleaseError("unsupported image catalog schema version")
        return catalog

    def _load_image_state(self) -> dict[str, Any]:
        existing = self.store.read_json(self.image_state_path)
        if existing:
            return existing
        return {
            "schema_version": SCHEMA_VERSION,
            "accepted": {},
            "attempts": {},
            "rejections": {},
            "metrics": {
                "image_attempts": 0,
                "retries": 0,
                "rejections": 0,
                "acceptances": 0,
                "accepted_image_reuse": 0,
                "injected_failures": 0,
            },
        }

    def _save_image_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.image_state_path, state)

    def _write_metrics(self, section: str, metrics: dict[str, Any]) -> None:
        current = self.store.read_json(self.metrics_path) or {"schema_version": SCHEMA_VERSION}
        current[section] = deepcopy(metrics)
        current[section]["recorded_at"] = utc_now()
        self.store._atomic_write(self.metrics_path, current)

    def _quality_errors(self, fixture: dict[str, Any], policy: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        if fixture.get("format") not in policy["allowed_formats"]:
            errors.append("format")
        if fixture.get("width") != policy["width"] or fixture.get("height") != policy["height"]:
            errors.append("dimensions")
        required_true = (
            "professional_textbook_editorial",
            "story_specific",
            "mechanism_explanatory",
            "high_detail",
            "high_information_density",
            "white_background",
        )
        for key in required_true:
            if fixture.get(key) is not True:
                errors.append(key)
        prohibited_true = (
            "sparse_generic_box_arrow",
            "reused_composition",
            "photo",
            "people",
            "decorative_collage",
            "clipped_text",
            "overlapping_text",
        )
        for key in prohibited_true:
            if fixture.get(key) is True:
                errors.append(key)
        if not fixture.get("mechanism_summary"):
            errors.append("mechanism_summary")
        if not fixture.get("composition_id"):
            errors.append("composition_id")
        return errors

    def _accepted_record(
        self,
        story: dict[str, Any],
        fixture: dict[str, Any],
        catalog_digest: str,
    ) -> dict[str, Any]:
        story_input_digest = digest(story)
        binary_digest = digest(
            {
                "binary_seed": fixture["binary_seed"],
                "story_input_digest": story_input_digest,
                "catalog_digest": catalog_digest,
            }
        )
        return {
            "story_id": story["story_id"],
            "image_id": fixture["image_id"],
            "accepted": True,
            "format": fixture["format"],
            "width": fixture["width"],
            "height": fixture["height"],
            "binary_digest": binary_digest,
            "composition_id": fixture["composition_id"],
            "mechanism_summary": fixture["mechanism_summary"],
            "quality": {
                "professional_textbook_editorial": True,
                "story_specific": True,
                "mechanism_explanatory": True,
                "high_detail": True,
                "high_information_density": True,
                "white_background": True,
                "no_sparse_generic_fallback": True,
                "no_reused_composition_substitute": True,
                "no_photo_people_collage": True,
                "no_clipped_or_overlapping_text": True,
            },
            "provenance": {
                "adapter": "deterministic-synthetic-image-fixture-v1",
                "catalog_digest": catalog_digest,
                "story_input_digest": story_input_digest,
            },
        }

    def build_images(self) -> dict[str, Any]:
        started = time.monotonic()
        edition = self.store.load_artifact("edition")
        if not edition or edition.get("status") != "locked":
            raise PreReleaseError("locked edition required before image completion")
        catalog = self._catalog()
        catalog_digest = digest(catalog)
        policy = catalog["policy"]
        max_attempts = int(policy["max_attempts_per_image"])
        stories = edition["data"]["stories"]
        fixtures = {x["story_id"]: x for x in catalog["images"]}
        story_ids = [x["story_id"] for x in stories]
        if set(fixtures) != set(story_ids) or len(story_ids) != 6:
            raise PreReleaseError("image catalog must bind exactly the six locked stories")

        state = self._load_image_state()
        for story in stories:
            story_id = story["story_id"]
            fixture = fixtures[story_id]
            expected_story_digest = digest(story)
            existing = state["accepted"].get(story_id)
            if (
                existing
                and existing.get("provenance", {}).get("story_input_digest") == expected_story_digest
                and existing.get("provenance", {}).get("catalog_digest") == catalog_digest
            ):
                state["metrics"]["accepted_image_reuse"] += 1
                self._save_image_state(state)
                continue
            if existing:
                state["accepted"].pop(story_id, None)

            while story_id not in state["accepted"]:
                prior_attempts = int(state["attempts"].get(story_id, 0))
                if prior_attempts >= max_attempts:
                    raise PreReleaseError(f"bounded image retry exhausted for {story_id}")
                attempt_no = prior_attempts + 1
                state["attempts"][story_id] = attempt_no
                state["metrics"]["image_attempts"] += 1
                if attempt_no > 1:
                    state["metrics"]["retries"] += 1
                self._save_image_state(state)

                target = (self.failure_boundary_id or "").removeprefix("image:")
                if target == story_id and not self._failure_fired:
                    self._failure_fired = True
                    state["metrics"]["injected_failures"] += 1
                    self._save_image_state(state)
                    self._write_metrics("images", state["metrics"])
                    raise ImageBoundaryFailure(story_id, self.failure_class)

                accept_on_attempt = int(fixture.get("accept_on_attempt", 1))
                if attempt_no < accept_on_attempt:
                    state["metrics"]["rejections"] += 1
                    state["rejections"].setdefault(story_id, []).append("synthetic_quality_retry")
                    self._save_image_state(state)
                    continue

                errors = self._quality_errors(fixture, policy)
                if errors:
                    state["metrics"]["rejections"] += 1
                    state["rejections"].setdefault(story_id, []).append(
                        "quality_contract:" + ",".join(sorted(errors))
                    )
                    self._save_image_state(state)
                    continue

                state["accepted"][story_id] = self._accepted_record(story, fixture, catalog_digest)
                state["metrics"]["acceptances"] += 1
                self._save_image_state(state)

        accepted = [state["accepted"][story_id] for story_id in story_ids]
        if len(accepted) != 6 or len({x["story_id"] for x in accepted}) != 6:
            raise PreReleaseError("exactly six unique accepted story images are required")
        compositions = [x["composition_id"] for x in accepted]
        if len(set(compositions)) != 6:
            raise PreReleaseError("accepted images must use six story-specific compositions")

        metrics = deepcopy(state["metrics"])
        metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._write_metrics("images", metrics)
        return {
            "image_contract_version": self.IMAGE_CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "accepted_count": 6,
            "quality_contract": {
                "professional_textbook_editorial": True,
                "story_specific_mechanism_explanatory": True,
                "high_detail_information_density": True,
                "white_background": True,
                "target_dimensions": [1200, 630],
                "preferred_format": "webp",
                "generic_sparse_fallback_allowed": False,
                "reused_composition_allowed": False,
                "photos_people_decorative_collage_allowed": False,
                "clipped_or_overlapping_text_allowed": False,
            },
            "images": accepted,
        }

    def _fail(self, invariant: str, message: str) -> None:
        raise ValidationBoundaryFailure(invariant, message)

    def _require_locked(self, artifact_type: str) -> dict[str, Any]:
        record = self.store.load_artifact(artifact_type)
        if not record:
            self._fail(f"{artifact_type}.present", "required artifact missing")
        if record.get("status") != "locked":
            self._fail(f"{artifact_type}.locked", "required artifact is not locked")
        if record.get("schema_version") != SCHEMA_VERSION:
            self._fail(f"{artifact_type}.schema", "unsupported schema version")
        if record.get("edition_date") != self.edition_date:
            self._fail(f"{artifact_type}.date", "stale or wrong-date artifact")
        if record.get("content_digest") != semantic_digest(record):
            self._fail(f"{artifact_type}.digest", "content digest does not match semantic record")
        expected_inputs = []
        for dependency in ARTIFACT_DEPENDENCIES[artifact_type]:
            dependency_record = self.store.load_artifact(dependency)
            if not dependency_record or dependency_record.get("status") != "locked":
                self._fail(f"{artifact_type}.inputs", f"dependency {dependency} is not locked")
            expected_inputs.append(dependency_record["content_digest"])
        if sorted(record.get("input_digests", [])) != sorted(expected_inputs):
            self._fail(f"{artifact_type}.inputs", "locked input digests do not match dependencies")
        return record

    def build_validation_bundle(self) -> dict[str, Any]:
        started = time.monotonic()
        records = {name: self._require_locked(name) for name in self.REQUIRED_BUNDLE_INPUTS}

        edition = records["edition"]["data"]
        stories = edition.get("stories", [])
        if len(stories) != 6:
            self._fail("edition.story_count", "exactly six stories required")
        if [x.get("presentation_position") for x in stories] != list(range(1, 7)):
            self._fail("edition.order", "stories must be ordered 1 through 6")
        category_counts = {
            category: sum(x.get("category_id") == category for x in stories)
            for category in self.EXPECTED_CATEGORIES
        }
        if category_counts != self.EXPECTED_CATEGORIES:
            self._fail("edition.allocation", "exact 2/2/2 allocation required")
        if sum(bool(x.get("agent_skills")) for x in stories) != 1:
            self._fail("edition.agent_skills", "exactly one reusable Agent Skills story required")

        media = records["media"]["data"]
        videos = media.get("videos", [])
        podcasts = media.get("podcasts", [])
        if len(videos) != 2 or not all(x.get("verified") for x in videos):
            self._fail("media.videos", "exactly two verified videos required")
        if len(podcasts) != 2 or not all(x.get("verified") for x in podcasts):
            self._fail("media.podcasts", "exactly two verified podcasts required")

        images = records["images"]["data"]
        accepted_images = images.get("images", [])
        story_ids = [x["story_id"] for x in stories]
        image_story_ids = [x.get("story_id") for x in accepted_images]
        if images.get("accepted_count") != 6 or len(accepted_images) != 6:
            self._fail("images.count", "exactly six accepted images required")
        if len(set(image_story_ids)) != 6 or set(image_story_ids) != set(story_ids):
            self._fail("images.binding", "one unique accepted image must bind each locked story")
        if not all(x.get("accepted") is True for x in accepted_images):
            self._fail("images.acceptance", "all six images must be accepted")
        if len({x.get("composition_id") for x in accepted_images}) != 6:
            self._fail("images.composition", "story-specific compositions must be unique")
        for story, image in zip(stories, accepted_images):
            if image.get("story_id") != story.get("story_id"):
                self._fail("images.order", "image order must match locked edition order")
            if image.get("provenance", {}).get("story_input_digest") != digest(story):
                self._fail("images.provenance", "image story provenance digest mismatch")

        watchlist = records["watchlist"]["data"]
        if watchlist.get("edition_date") != self.edition_date:
            self._fail("watchlist.date", "Watchlist delta must be current for edition date")

        bridges = records["book-bridges"]["data"].get("decisions", [])
        bridge_story_ids = [x.get("story_id") for x in bridges]
        if len(bridges) != 6 or len(set(bridge_story_ids)) != 6 or set(bridge_story_ids) != set(story_ids):
            self._fail("book_bridges.count", "exactly six bridge decisions required")
        if not all(x.get("decision") in {"bridge", "no_bridge"} for x in bridges):
            self._fail("book_bridges.decision", "bridge decision must be bridge or no_bridge")

        rating = records["rating-contract"]["data"]
        if rating.get("contract_version") != RATING_CONTRACT_VERSION:
            self._fail("rating.contract", "five-star-v1 rating contract required")

        checks = {
            "edition_exact_2_2_2": True,
            "edition_exactly_one_agent_skills": True,
            "media_exactly_two_verified_videos": True,
            "media_exactly_two_verified_podcasts": True,
            "images_exactly_six_accepted": True,
            "images_one_per_story": True,
            "watchlist_date_current": True,
            "book_bridges_exactly_six": True,
            "book_bridges_explicit_no_bridge_valid": True,
            "rating_contract_five_star_v1": True,
            "artifact_dates_current": True,
            "artifact_schema_versions_supported": True,
            "artifact_content_digests_valid": True,
            "artifact_input_digests_current": True,
        }
        inputs = {name: records[name]["content_digest"] for name in self.REQUIRED_BUNDLE_INPUTS}
        metrics = {
            "validation_checks": len(checks),
            "validation_failures": 0,
            "bundle_reuse_eligible": True,
            "elapsed_ms": max(0, int((time.monotonic() - started) * 1000)),
        }
        self._write_metrics("validation", metrics)
        return {
            "bundle_contract_version": self.BUNDLE_CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "validation_result": "passed",
            "validation_checks": checks,
            "ordered_input_digests": inputs,
            "release_authorized": False,
            "validation_only_boundary": True,
        }
