from __future__ import annotations

import html
import json
import time
from copy import deepcopy
from pathlib import Path
from typing import Any

from .contracts import ARTIFACT_DEPENDENCIES, RATING_CONTRACT_VERSION, SCHEMA_VERSION
from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now


class ReaderRenderError(ContractError):
    pass


class RenderBoundaryFailure(ReaderRenderError):
    def __init__(self, boundary_type: str, boundary_id: str, message: str):
        super().__init__(message)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = f"render:{boundary_id}"


class ReaderSurfaceRenderer:
    RENDER_CONTRACT_VERSION = "1.0.0"
    MANIFEST_CONTRACT_VERSION = "1.0.0"

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        mode: str,
        fixture_root: Path | str | None,
        *,
        failure_boundary_id: str | None = None,
        failure_class: str = "synthetic_render_boundary_failure",
    ):
        self.store = store
        self.edition_date = edition_date
        self.mode = mode
        self.fixture_root = Path(fixture_root) if fixture_root is not None else None
        self.failure_boundary_id = (failure_boundary_id or "").removeprefix("render:")
        self.failure_class = failure_class
        self._failure_fired = False
        self.state_path = self.store.run_dir / "reader-render-state.json"
        self.metrics_path = self.store.run_dir / "iteration5-metrics.json"
        self.output_dir = self.store.run_dir / "reader-renders"

    def _contract(self) -> dict[str, Any]:
        if self.fixture_root is None:
            raise ReaderRenderError(
                "production reader rendering is intentionally fail-closed: "
                "no approved zero-incremental-cost rendering/hosting adapter is configured"
            )
        path = self.fixture_root / "render-contract.json"
        if not path.exists():
            raise ReaderRenderError(f"missing Iteration 5 render contract fixture: {path}")
        contract = json.loads(path.read_text(encoding="utf-8"))
        if contract.get("schema_version") != SCHEMA_VERSION:
            raise ReaderRenderError("unsupported render contract schema version")
        if contract.get("render_contract_version") != self.RENDER_CONTRACT_VERSION:
            raise ReaderRenderError("unsupported render contract version")
        return contract

    def _load_state(self) -> dict[str, Any]:
        state = self.store.read_json(self.state_path)
        if state:
            return state
        return {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "attempts": {},
            "outputs": {},
            "metrics": {
                "route_attempts": 0,
                "route_retries": 0,
                "route_rejections": 0,
                "route_completions": 0,
                "route_cache_reuse": 0,
                "archive_feed_attempts": 0,
                "archive_feed_cache_reuse": 0,
                "injected_failures": 0,
                "per_route_cache_reuse": {},
            },
        }

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _write_metrics(self, section: str, values: dict[str, Any]) -> None:
        current = self.store.read_json(self.metrics_path) or {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
        }
        current[section] = deepcopy(values)
        current[section]["recorded_at"] = utc_now()
        self.store._atomic_write(self.metrics_path, current)

    def _fail(self, boundary_type: str, boundary_id: str, message: str) -> None:
        raise RenderBoundaryFailure(boundary_type, boundary_id, message)

    def _require_bundle(self) -> tuple[dict[str, Any], dict[str, dict[str, Any]]]:
        bundle = self.store.load_artifact("publication-bundle")
        if not bundle:
            self._fail("render_validation", "publication-bundle", "locked Iteration 4 bundle is missing")
        if bundle.get("status") != "locked":
            self._fail("render_validation", "publication-bundle", "publication bundle is not locked")
        if bundle.get("schema_version") != SCHEMA_VERSION:
            self._fail("render_validation", "publication-bundle", "publication bundle schema is incompatible")
        if bundle.get("edition_date") != self.edition_date:
            self._fail("render_validation", "publication-bundle", "publication bundle is stale or wrong-date")
        if bundle.get("content_digest") != semantic_digest(bundle):
            self._fail("render_validation", "publication-bundle", "publication bundle semantic digest mismatch")
        data = bundle.get("data", {})
        if data.get("validation_result") != "passed":
            self._fail("render_validation", "publication-bundle", "publication bundle validation did not pass")
        if data.get("release_authorized") is not False:
            self._fail("render_validation", "publication-bundle", "release_authorized must remain false")

        records: dict[str, dict[str, Any]] = {}
        ordered = data.get("ordered_input_digests", {})
        expected_names = ARTIFACT_DEPENDENCIES["publication-bundle"]
        if set(ordered) != set(expected_names):
            self._fail("render_validation", "publication-bundle", "publication bundle input map is incomplete")
        for name in expected_names:
            record = self.store.load_artifact(name)
            if not record or record.get("status") != "locked":
                self._fail("render_validation", name, f"locked {name} input is missing")
            if record.get("schema_version") != SCHEMA_VERSION:
                self._fail("render_validation", name, f"{name} schema is incompatible")
            if record.get("edition_date") != self.edition_date:
                self._fail("render_validation", name, f"{name} is stale or wrong-date")
            if record.get("content_digest") != semantic_digest(record):
                self._fail("render_validation", name, f"{name} semantic digest mismatch")
            if ordered.get(name) != record.get("content_digest"):
                self._fail("render_validation", name, f"{name} digest differs from locked publication bundle")
            records[name] = record
        if sorted(bundle.get("input_digests", [])) != sorted(ordered.values()):
            self._fail("render_validation", "publication-bundle", "publication bundle dependency digests are inconsistent")
        return bundle, records

    def _bound_semantics(self, records: dict[str, dict[str, Any]]) -> dict[str, Any]:
        stories = sorted(
            records["edition"]["data"].get("stories", []),
            key=lambda x: int(x.get("presentation_position", 0)),
        )
        if len(stories) != 6 or [x.get("presentation_position") for x in stories] != list(range(1, 7)):
            self._fail("render_validation", "story-order", "exact six-story presentation order is required")
        story_ids = [x["story_id"] for x in stories]

        media = records["media"]["data"]
        videos = media.get("videos", [])
        podcasts = media.get("podcasts", [])
        if len(videos) != 2 or len(podcasts) != 2 or not all(
            item.get("verified") for item in videos + podcasts
        ):
            self._fail("render_validation", "media", "exactly two verified videos and two verified podcasts are required")

        watch = records["watchlist"]["data"]
        if watch.get("edition_date") != self.edition_date:
            self._fail("render_validation", "watchlist", "Watchlist summary is not current")
        expected_counts = {
            key: len(watch.get(key, []))
            for key in ("new_today", "updated_today", "carried_forward")
        }
        if watch.get("counts") != expected_counts:
            self._fail("render_validation", "watchlist", "Watchlist counts do not match locked topic lists")

        bridges = records["book-bridges"]["data"].get("decisions", [])
        if len(bridges) != 6 or [x.get("story_id") for x in bridges] != story_ids:
            self._fail("render_validation", "book-bridges", "bridge decisions must preserve exact story order")
        if not all(x.get("decision") in {"bridge", "no_bridge"} for x in bridges):
            self._fail("render_validation", "book-bridges", "bridge decision was changed or fabricated")

        images = records["images"]["data"].get("images", [])
        if len(images) != 6 or [x.get("story_id") for x in images] != story_ids:
            self._fail("render_validation", "images", "image/story bindings must preserve exact story order")
        if not all(x.get("accepted") is True for x in images):
            self._fail("render_validation", "images", "all six images must remain accepted")

        rating = records["rating-contract"]["data"]
        if rating.get("contract_version") != RATING_CONTRACT_VERSION:
            self._fail("render_validation", "rating-contract", "five-star-v1 contract is required")

        return {
            "stories": stories,
            "story_ids": story_ids,
            "videos": videos,
            "podcasts": podcasts,
            "watchlist": watch,
            "watchlist_counts": expected_counts,
            "bridges": bridges,
            "images": images,
            "rating_contract": rating,
        }

    def _bridge_html(self, decision: dict[str, Any]) -> str:
        story_id = html.escape(str(decision["story_id"]))
        if decision["decision"] == "bridge":
            return (
                f'<aside class="professional-series-bridge" data-story-id="{story_id}" '
                f'data-decision="bridge"><a href="{html.escape(str(decision["series_url"]))}">'
                f'{html.escape(str(decision["book_id"]))}: {html.escape(str(decision["section"]))}</a></aside>'
            )
        return (
            f'<aside class="professional-series-bridge" data-story-id="{story_id}" '
            'data-decision="no_bridge"><span>No Professional Series bridge for this story.</span></aside>'
        )

    def _rating_html(self, story_id: str) -> str:
        return (
            f'<div class="rating-share-hooks" data-story-id="{html.escape(story_id)}" '
            f'data-rating-contract="{RATING_CONTRACT_VERSION}" data-rating-state="missing" '
            'data-share-sender-rating="suppressed"></div>'
        )

    def _story_card(
        self,
        story: dict[str, Any],
        image: dict[str, Any],
        bridge: dict[str, Any],
    ) -> str:
        title = html.escape(str(story["title"]))
        story_id = html.escape(str(story["story_id"]))
        route = f'/{self.edition_date}/stories/{story_id}/'
        return (
            f'<li data-position="{story["presentation_position"]}" data-story-id="{story_id}">'
            f'<article><img src="/shadow/images/{html.escape(str(image["image_id"]))}.{html.escape(str(image["format"]))}" '
            f'alt="{title} mechanism illustration" data-image-digest="{html.escape(str(image["binary_digest"]))}">'
            f'<h2><a href="{route}">{title}</a></h2>'
            f'<a class="source" href="{html.escape(str(story["url"]))}">Authoritative source</a>'
            f'{self._bridge_html(bridge)}{self._rating_html(story["story_id"])}</article></li>'
        )

    def _edition_html(self, surface: str, sem: dict[str, Any]) -> str:
        cards = "".join(
            self._story_card(story, image, bridge)
            for story, image, bridge in zip(sem["stories"], sem["images"], sem["bridges"])
        )
        videos = "".join(
            f'<li data-media-id="{html.escape(str(x["media_id"]))}"><a href="{html.escape(str(x["url"]))}">{html.escape(str(x["title"]))}</a></li>'
            for x in sem["videos"]
        )
        podcasts = "".join(
            f'<li data-media-id="{html.escape(str(x["media_id"]))}"><a href="{html.escape(str(x["url"]))}">{html.escape(str(x["title"]))}</a></li>'
            for x in sem["podcasts"]
        )
        c = sem["watchlist_counts"]
        return (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<title>Daily AI Brief {self.edition_date}</title></head><body>'
            f'<main data-surface="{html.escape(surface)}" data-edition-date="{self.edition_date}">'
            f'<h1>Daily AI Brief — {self.edition_date}</h1><ol class="stories">{cards}</ol>'
            f'<section aria-labelledby="media-heading"><h2 id="media-heading">Media</h2>'
            f'<h3>Videos</h3><ol class="videos">{videos}</ol><h3>Podcasts</h3><ol class="podcasts">{podcasts}</ol></section>'
            f'<section aria-labelledby="watchlist-heading"><h2 id="watchlist-heading">Emerging AI Watchlist</h2>'
            f'<p data-new="{c["new_today"]}" data-updated="{c["updated_today"]}" '
            f'data-carried="{c["carried_forward"]}">{c["new_today"]} new today · '
            f'{c["updated_today"]} updated · {c["carried_forward"]} carried forward</p></section>'
            '</main></body></html>'
        )

    def _story_html(
        self,
        story: dict[str, Any],
        image: dict[str, Any],
        bridge: dict[str, Any],
        story_order: list[str],
    ) -> str:
        title = html.escape(str(story["title"]))
        navigation = "".join(
            f'<li data-story-id="{html.escape(story_id)}"><a href="/{self.edition_date}/stories/{html.escape(story_id)}/">{html.escape(story_id)}</a></li>'
            for story_id in story_order
        )
        return (
            '<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<title>{title} — Daily AI Brief</title></head><body>'
            f'<main data-surface="story" data-story-id="{html.escape(str(story["story_id"]))}" '
            f'data-position="{story["presentation_position"]}"><h1>{title}</h1>'
            f'<img src="/shadow/images/{html.escape(str(image["image_id"]))}.{html.escape(str(image["format"]))}" '
            f'alt="{title} mechanism illustration" data-image-digest="{html.escape(str(image["binary_digest"]))}">'
            f'<p><a class="source" href="{html.escape(str(story["url"]))}">Authoritative source</a></p>'
            f'{self._bridge_html(bridge)}{self._rating_html(story["story_id"])}'
            f'<nav aria-label="Edition story order"><ol>{navigation}</ol></nav>'
            '</main></body></html>'
        )

    def _archive_html(self, story_ids: list[str]) -> str:
        items = "".join(
            f'<li data-story-id="{html.escape(story_id)}"><a href="/{self.edition_date}/stories/{html.escape(story_id)}/">{html.escape(story_id)}</a></li>'
            for story_id in story_ids
        )
        return (
            '<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Daily AI Brief Archive</title></head>'
            f'<body><main data-surface="archive"><h1>Archive</h1><article data-edition-date="{self.edition_date}">'
            f'<h2><a href="/{self.edition_date}/">{self.edition_date}</a></h2><ol>{items}</ol></article></main></body></html>'
        )

    def _feed_xml(self, stories: list[dict[str, Any]]) -> str:
        items = "".join(
            '<item>'
            f'<title>{html.escape(str(story["title"]))}</title>'
            f'<link>/{self.edition_date}/stories/{html.escape(str(story["story_id"]))}/</link>'
            f'<guid>{self.edition_date}:{html.escape(str(story["story_id"]))}</guid>'
            f'<category>{html.escape(str(story["category_id"]))}</category>'
            '</item>'
            for story in stories
        )
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<rss version="2.0"><channel><title>Daily AI Brief</title>'
            f'<description>Edition {self.edition_date}</description><link>/{self.edition_date}/</link>{items}</channel></rss>'
        )

    def _validate_output(self, output: dict[str, Any]) -> dict[str, bool]:
        content = output["content"]
        if output["content_type"] == "text/html":
            checks = {
                "has_html_lang": '<html lang="en">' in content,
                "has_main": "<main" in content,
                "has_h1": "<h1" in content,
                "images_have_alt": content.count("<img ") == content.count(' alt="'),
            }
        else:
            checks = {
                "rss_root": content.startswith('<?xml version="1.0" encoding="UTF-8"?><rss'),
                "rss_channel": "<channel>" in content and "</channel>" in content,
            }
        if not all(checks.values()):
            self._fail("render_validation", output["route_id"], "structural/accessibility validation failed")
        return checks

    def _expected_outputs(self, sem: dict[str, Any]) -> list[dict[str, Any]]:
        outputs: list[dict[str, Any]] = []
        story_ids = sem["story_ids"]
        for route_id, route, surface in (
            ("current", "/", "current"),
            ("latest", "/latest/", "latest"),
            ("dated", f"/{self.edition_date}/", "dated"),
        ):
            outputs.append({
                "route_id": route_id,
                "route": route,
                "kind": "edition",
                "content_type": "text/html",
                "content": self._edition_html(surface, sem),
                "semantic": {
                    "surface": surface,
                    "story_ids": story_ids,
                    "video_ids": [x["media_id"] for x in sem["videos"]],
                    "podcast_ids": [x["media_id"] for x in sem["podcasts"]],
                    "watchlist_counts": deepcopy(sem["watchlist_counts"]),
                    "bridge_decisions": deepcopy(sem["bridges"]),
                    "image_bindings": [
                        {"story_id": x["story_id"], "image_id": x["image_id"], "binary_digest": x["binary_digest"]}
                        for x in sem["images"]
                    ],
                    "rating_contract": RATING_CONTRACT_VERSION,
                    "stored_rating_values": None,
                },
            })
        for story, image, bridge in zip(sem["stories"], sem["images"], sem["bridges"]):
            outputs.append({
                "route_id": f'story:{story["story_id"]}',
                "route": f'/{self.edition_date}/stories/{story["story_id"]}/',
                "kind": "story",
                "content_type": "text/html",
                "content": self._story_html(story, image, bridge, story_ids),
                "semantic": {
                    "surface": "story",
                    "story_id": story["story_id"],
                    "presentation_position": story["presentation_position"],
                    "edition_story_order": story_ids,
                    "bridge_decision": deepcopy(bridge),
                    "image_binding": {
                        "story_id": image["story_id"],
                        "image_id": image["image_id"],
                        "binary_digest": image["binary_digest"],
                    },
                    "rating_contract": RATING_CONTRACT_VERSION,
                    "stored_rating_value": None,
                },
            })
        outputs.append({
            "route_id": "archive",
            "route": "/archive/",
            "kind": "archive",
            "content_type": "text/html",
            "content": self._archive_html(story_ids),
            "semantic": {
                "surface": "archive",
                "edition_membership": [self.edition_date],
                "story_ids": story_ids,
            },
        })
        outputs.append({
            "route_id": "feed",
            "route": "/feed.xml",
            "kind": "feed",
            "content_type": "application/rss+xml",
            "content": self._feed_xml(sem["stories"]),
            "semantic": {
                "surface": "feed",
                "edition_membership": [self.edition_date],
                "story_ids": story_ids,
            },
        })
        return outputs

    def _output_digest(self, output: dict[str, Any]) -> str:
        return digest({
            "route": output["route"],
            "content_type": output["content_type"],
            "content": output["content"],
            "semantic": output["semantic"],
        })

    def _persist_output(self, record: dict[str, Any]) -> None:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        safe = record["route_id"].replace(":", "__")
        self.store._atomic_write(self.output_dir / f"{safe}.json", record)

    def build_reader_render(self) -> dict[str, Any]:
        started = time.monotonic()
        contract = self._contract()
        contract_digest = digest(contract)
        bundle, records = self._require_bundle()
        sem = self._bound_semantics(records)
        expected = self._expected_outputs(sem)
        state = self._load_state()

        for output in expected:
            route_id = output["route_id"]
            output["structural_checks"] = self._validate_output(output)
            output_digest = self._output_digest(output)
            existing = state["outputs"].get(route_id)
            if (
                existing
                and existing.get("output_digest") == output_digest
                and existing.get("template_digest") == contract_digest
                and existing.get("publication_bundle_digest") == bundle["content_digest"]
            ):
                state["metrics"]["route_cache_reuse"] += 1
                state["metrics"]["per_route_cache_reuse"][route_id] = (
                    state["metrics"]["per_route_cache_reuse"].get(route_id, 0) + 1
                )
                if output["kind"] in {"archive", "feed"}:
                    state["metrics"]["archive_feed_cache_reuse"] += 1
                self._save_state(state)
                continue

            attempt = int(state["attempts"].get(route_id, 0)) + 1
            state["attempts"][route_id] = attempt
            state["metrics"]["route_attempts"] += 1
            if attempt > 1:
                state["metrics"]["route_retries"] += 1
            if output["kind"] in {"archive", "feed"}:
                state["metrics"]["archive_feed_attempts"] += 1
            self._save_state(state)

            if self.failure_boundary_id == route_id and not self._failure_fired:
                self._failure_fired = True
                state["metrics"]["injected_failures"] += 1
                self._save_state(state)
                metrics = deepcopy(state["metrics"])
                metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
                self._write_metrics("rendering", metrics)
                boundary_type = "archive_feed" if output["kind"] in {"archive", "feed"} else "route"
                raise RenderBoundaryFailure(boundary_type, route_id, self.failure_class)

            record = {
                "schema_version": SCHEMA_VERSION,
                "render_contract_version": self.RENDER_CONTRACT_VERSION,
                "template_version": contract["template_version"],
                "template_digest": contract_digest,
                "publication_bundle_digest": bundle["content_digest"],
                "edition_date": self.edition_date,
                "route_id": route_id,
                "route": output["route"],
                "kind": output["kind"],
                "content_type": output["content_type"],
                "content": output["content"],
                "semantic": output["semantic"],
                "structural_checks": output["structural_checks"],
                "output_digest": output_digest,
            }
            state["outputs"][route_id] = record
            state["metrics"]["route_completions"] += 1
            self._persist_output(record)
            self._save_state(state)

        ordered = [state["outputs"][output["route_id"]] for output in expected]
        route_ids = [x["route_id"] for x in ordered]
        if len(ordered) != 11 or len(set(route_ids)) != 11:
            self._fail("render_validation", "route-set", "exactly eleven required shadow/static outputs are required")
        if not all(all(x["structural_checks"].values()) for x in ordered):
            self._fail("render_validation", "accessibility", "one or more render outputs failed structural checks")

        metrics = deepcopy(state["metrics"])
        metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._write_metrics("rendering", metrics)
        return {
            "render_contract_version": self.RENDER_CONTRACT_VERSION,
            "template_version": contract["template_version"],
            "template_digest": contract_digest,
            "edition_date": self.edition_date,
            "publication_bundle_digest": bundle["content_digest"],
            "story_order": sem["story_ids"],
            "media": {
                "video_ids": [x["media_id"] for x in sem["videos"]],
                "podcast_ids": [x["media_id"] for x in sem["podcasts"]],
            },
            "watchlist_counts": deepcopy(sem["watchlist_counts"]),
            "bridge_decisions": deepcopy(sem["bridges"]),
            "image_bindings": [
                {"story_id": x["story_id"], "image_id": x["image_id"], "binary_digest": x["binary_digest"]}
                for x in sem["images"]
            ],
            "rating_contract": {
                "contract_version": sem["rating_contract"]["contract_version"],
                "stored_rating_values": None,
                "fabricated_rating_values": False,
            },
            "archive_membership": [self.edition_date],
            "feed_membership": [self.edition_date],
            "routes": ordered,
            "release_authorized": False,
            "render_only_boundary": True,
        }

    def build_route_manifest(self) -> dict[str, Any]:
        started = time.monotonic()
        contract = self._contract()
        contract_digest = digest(contract)
        bundle, records = self._require_bundle()
        sem = self._bound_semantics(records)
        reader = self.store.load_artifact("reader-render")
        metrics = self.store.read_json(self.metrics_path) or {
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
        }
        manifest_metrics = deepcopy(metrics.get("manifest", {}))
        manifest_metrics.setdefault("attempts", 0)
        manifest_metrics.setdefault("validation_checks", 0)
        manifest_metrics.setdefault("validation_failures", 0)
        manifest_metrics.setdefault("injected_failures", 0)
        manifest_metrics["attempts"] += 1

        def reject(boundary_id: str, message: str) -> None:
            manifest_metrics["validation_failures"] += 1
            self._write_metrics("manifest", manifest_metrics)
            self._fail("manifest_validation", boundary_id, message)

        if not reader or reader.get("status") != "locked":
            reject("reader-render", "locked reader-render artifact is missing")
        if reader.get("content_digest") != semantic_digest(reader):
            reject("reader-render", "reader-render semantic digest mismatch")
        if reader.get("edition_date") != self.edition_date:
            reject("reader-render", "reader-render is stale or wrong-date")
        if reader.get("input_digests") != [bundle["content_digest"]]:
            reject("reader-render", "reader-render input does not bind the locked publication bundle")

        data = reader["data"]
        checks = {
            "publication_bundle_digest": data.get("publication_bundle_digest") == bundle["content_digest"],
            "template_digest": data.get("template_digest") == contract_digest,
            "template_version": data.get("template_version") == contract["template_version"],
            "story_order": data.get("story_order") == sem["story_ids"],
            "media_videos": data.get("media", {}).get("video_ids") == [x["media_id"] for x in sem["videos"]],
            "media_podcasts": data.get("media", {}).get("podcast_ids") == [x["media_id"] for x in sem["podcasts"]],
            "watchlist": data.get("watchlist_counts") == sem["watchlist_counts"],
            "bridges": data.get("bridge_decisions") == sem["bridges"],
            "images": data.get("image_bindings") == [
                {"story_id": x["story_id"], "image_id": x["image_id"], "binary_digest": x["binary_digest"]}
                for x in sem["images"]
            ],
            "rating_contract": data.get("rating_contract", {}).get("contract_version") == RATING_CONTRACT_VERSION,
            "no_fabricated_ratings": data.get("rating_contract", {}).get("fabricated_rating_values") is False
            and data.get("rating_contract", {}).get("stored_rating_values") is None,
            "archive_membership": data.get("archive_membership") == [self.edition_date],
            "feed_membership": data.get("feed_membership") == [self.edition_date],
            "release_authorized_false": data.get("release_authorized") is False,
        }
        routes = data.get("routes", [])
        expected_route_ids = [
            "current", "latest", "dated",
            *[f"story:{story_id}" for story_id in sem["story_ids"]],
            "archive", "feed",
        ]
        checks["route_count"] = len(routes) == 11
        checks["route_ids"] = [x.get("route_id") for x in routes] == expected_route_ids
        checks["route_uniqueness"] = len({x.get("route") for x in routes}) == 11
        checks["structural_accessibility"] = all(
            bool(x.get("structural_checks")) and all(x["structural_checks"].values()) for x in routes
        )

        for route in routes:
            expected_digest = digest({
                "route": route.get("route"),
                "content_type": route.get("content_type"),
                "content": route.get("content"),
                "semantic": route.get("semantic"),
            })
            if expected_digest != route.get("output_digest"):
                reject(route.get("route_id", "unknown-route"), "rendered output digest does not match content")
        checks["route_output_digests"] = True

        edition_routes = [x for x in routes if x.get("route_id") in {"current", "latest", "dated"}]
        checks["edition_surface_story_order"] = all(
            x.get("semantic", {}).get("story_ids") == sem["story_ids"] for x in edition_routes
        )
        story_routes = [x for x in routes if x.get("kind") == "story"]
        checks["story_surface_order_context"] = len(story_routes) == 6 and all(
            x.get("semantic", {}).get("edition_story_order") == sem["story_ids"] for x in story_routes
        )
        checks["story_surface_identity"] = [
            x.get("semantic", {}).get("story_id") for x in story_routes
        ] == sem["story_ids"]

        manifest_metrics["validation_checks"] = len(checks)
        failed = [name for name, value in checks.items() if not value]
        if failed:
            reject("manifest-validation", "manifest invariant failures: " + ",".join(sorted(failed)))

        if self.failure_boundary_id == "manifest-validation" and not self._failure_fired:
            self._failure_fired = True
            manifest_metrics["injected_failures"] += 1
            manifest_metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
            self._write_metrics("manifest", manifest_metrics)
            raise RenderBoundaryFailure("manifest_validation", "manifest-validation", self.failure_class)

        manifest_metrics["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._write_metrics("manifest", manifest_metrics)
        return {
            "manifest_contract_version": self.MANIFEST_CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "publication_bundle_digest": bundle["content_digest"],
            "reader_render_digest": reader["content_digest"],
            "render_contract_version": self.RENDER_CONTRACT_VERSION,
            "template_version": contract["template_version"],
            "template_digest": contract_digest,
            "routes": [
                {
                    "route_id": x["route_id"],
                    "route": x["route"],
                    "kind": x["kind"],
                    "content_type": x["content_type"],
                    "output_digest": x["output_digest"],
                    "structural_checks": deepcopy(x["structural_checks"]),
                }
                for x in routes
            ],
            "archive_membership": [self.edition_date],
            "feed_membership": [self.edition_date],
            "accessibility_structural_result": "passed",
            "validation_result": "passed",
            "validation_checks": checks,
            "release_authorized": False,
            "render_only_boundary": True,
        }
