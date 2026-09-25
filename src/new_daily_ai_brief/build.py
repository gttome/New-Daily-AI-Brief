from __future__ import annotations

import json
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from .store import CanonicalStore, ContractError, digest, utc_now


class BuildError(ContractError):
    pass


class BuildBoundaryFailure(RuntimeError):
    def __init__(self, boundary_type: str, boundary_id: str, failure_class: str):
        super().__init__(failure_class)
        self.boundary_type = boundary_type
        self.boundary_id = boundary_id
        self.candidate_id = boundary_id


@dataclass(frozen=True)
class BuildFailureInjection:
    boundary_id: str
    failure_class: str = "synthetic_build_boundary_failure"


class BuildStagePipeline:
    """Deterministic Iteration 3 enrichment inside the existing Building state."""

    CONTRACT_VERSION = "1.0.0"

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        fixture_root: Path | str,
        failure_injection: BuildFailureInjection | None = None,
    ):
        self.store = store
        self.edition_date = edition_date
        self.fixture_root = Path(fixture_root)
        self.failure_injection = failure_injection
        self._failure_fired = False
        self.media_registry = self._load_fixture("media-registry.json")
        self.media_catalog = self._load_fixture("media-catalog.json")
        self.watch_registry = self._load_fixture("watchlist-registry.json")
        self.watch_catalog = self._load_fixture("watchlist-catalog.json")
        self.bridge_map = self._load_fixture("book-bridge-map.json")

    def _load_fixture(self, name: str) -> dict[str, Any]:
        path = self.fixture_root / name
        if not path.exists():
            raise BuildError(f"missing Iteration 3 fixture: {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def _state_path(self, name: str) -> Path:
        return self.store.run_dir / f"{name}-state.json"

    def _metrics_path(self) -> Path:
        return self.store.run_dir / "build-metrics.json"

    def _load_state(self, name: str, initial: dict[str, Any]) -> dict[str, Any]:
        return self.store.read_json(self._state_path(name)) or deepcopy(initial)

    def _save_state(self, name: str, state: dict[str, Any]) -> None:
        self.store._atomic_write(self._state_path(name), state)

    def _packet(
        self,
        directory: str,
        packet_id: str,
        data: dict[str, Any],
        state_metrics: dict[str, Any],
    ) -> dict[str, Any]:
        path = self.store.run_dir / directory / f"{packet_id}.json"
        expected = digest(data)
        existing = self.store.read_json(path)
        if existing and existing.get("status") == "locked" and existing.get("content_digest") == expected:
            state_metrics["cache_reuse"] = state_metrics.get("cache_reuse", 0) + 1
            return existing
        record = {
            "schema_version": self.CONTRACT_VERSION,
            "packet_id": packet_id,
            "status": "locked",
            "content_digest": expected,
            "data": data,
            "locked_at": utc_now(),
        }
        self.store._atomic_write(path, record)
        return record

    def _maybe_fail(self, boundary_type: str, boundary_id: str, state_name: str, state: dict[str, Any]) -> None:
        if (
            self.failure_injection
            and not self._failure_fired
            and self.failure_injection.boundary_id == boundary_id
        ):
            self._failure_fired = True
            self._save_state(state_name, state)
            self._write_metrics()
            raise BuildBoundaryFailure(boundary_type, boundary_id, self.failure_injection.failure_class)

    def _edition(self) -> dict[str, Any]:
        edition = self.store.load_artifact("edition")
        if not edition or edition.get("status") != "locked":
            raise BuildError("locked edition is required before Building enrichment")
        return edition

    def _write_metrics(self) -> None:
        result: dict[str, Any] = {
            "schema_version": self.CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "recorded_at": utc_now(),
        }
        for name in ("media", "watchlist", "bridges"):
            state = self.store.read_json(self._state_path(name))
            result[name] = deepcopy(state.get("metrics", {})) if state else {}
        self.store._atomic_write(self._metrics_path(), result)

    def build_media(self) -> dict[str, Any]:
        started = time.monotonic()
        edition = self._edition()
        registry = self.media_registry
        catalog = {x["media_id"]: x for x in self.media_catalog["items"]}
        initial = {
            "schema_version": self.CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "checked": {},
            "selected": {"video": [], "podcast": []},
            "evidence_digests": {},
            "metrics": {
                "source_scans": 0,
                "candidate_checks": {"video": 0, "podcast": 0},
                "verification_attempts": 0,
                "availability_failures": 0,
                "fallback_sources_used": [],
                "cache_reuse": 0,
                "elapsed_ms": 0,
            },
        }
        state = self._load_state("media", initial)
        max_attempts = int(registry["policy"]["max_verification_attempts"])
        max_checks = int(registry["policy"]["max_candidate_checks_per_kind"])
        max_tier = int(registry["policy"]["max_fallback_tier"])

        sources = sorted(
            [s for s in registry["sources"] if s.get("enabled", True)],
            key=lambda s: (s["kind"], int(s["fallback_tier"]), int(s["priority"]), s["source_id"]),
        )
        scanned = set(state.get("scanned_sources", []))
        for kind in ("video", "podcast"):
            if len(state["selected"][kind]) >= 2:
                continue
            for tier in range(max_tier + 1):
                for source in [s for s in sources if s["kind"] == kind and int(s["fallback_tier"]) == tier]:
                    if source["source_id"] not in scanned:
                        state["metrics"]["source_scans"] += 1
                        scanned.add(source["source_id"])
                        state["scanned_sources"] = sorted(scanned)
                        self._save_state("media", state)
                    for media_id in source["candidate_ids"]:
                        if len(state["selected"][kind]) >= 2:
                            break
                        if media_id in state["checked"]:
                            state["metrics"]["cache_reuse"] += 1
                            continue
                        if state["metrics"]["candidate_checks"][kind] >= max_checks:
                            break
                        self._maybe_fail("media_item", media_id, "media", state)
                        candidate = deepcopy(catalog[media_id])
                        state["metrics"]["candidate_checks"][kind] += 1
                        verified = False
                        failures = int(candidate.get("synthetic_verification_failures", 0))
                        for attempt in range(1, max_attempts + 1):
                            state["metrics"]["verification_attempts"] += 1
                            if attempt <= failures:
                                continue
                            if candidate.get("available", False):
                                verified = True
                            break
                        packet_data = {
                            "packet_version": self.CONTRACT_VERSION,
                            "edition_date": self.edition_date,
                            "media_id": media_id,
                            "kind": kind,
                            "source_id": source["source_id"],
                            "fallback_tier": tier,
                            "title": candidate["title"],
                            "url": candidate["url"],
                            "published_at": candidate["published_at"],
                            "duration_minutes": candidate["duration_minutes"],
                            "verified": verified,
                            "provenance": {
                                "registry_version": registry["schema_version"],
                                "catalog_version": self.media_catalog["schema_version"],
                            },
                        }
                        packet = self._packet("media-evidence", media_id, packet_data, state["metrics"])
                        state["checked"][media_id] = "verified" if verified else "unavailable"
                        state["evidence_digests"][media_id] = packet["content_digest"]
                        if verified:
                            state["selected"][kind].append(media_id)
                            if tier > 0 and source["source_id"] not in state["metrics"]["fallback_sources_used"]:
                                state["metrics"]["fallback_sources_used"].append(source["source_id"])
                        else:
                            state["metrics"]["availability_failures"] += 1
                        self._save_state("media", state)
                    if len(state["selected"][kind]) >= 2:
                        break
                if len(state["selected"][kind]) >= 2:
                    break
            if len(state["selected"][kind]) != 2:
                raise BuildError(f"bounded media fallback could not produce exactly 2 {kind}s")

        state["scanned_sources"] = sorted(scanned)
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state("media", state)
        self._write_metrics()

        def selected(kind: str) -> list[dict[str, Any]]:
            values = []
            for media_id in state["selected"][kind]:
                c = catalog[media_id]
                values.append({
                    "media_id": media_id,
                    "kind": kind,
                    "title": c["title"],
                    "url": c["url"],
                    "published_at": c["published_at"],
                    "duration_minutes": c["duration_minutes"],
                    "verified": True,
                    "evidence_digest": state["evidence_digests"][media_id],
                })
            return values

        stable_metrics = deepcopy(state["metrics"])
        stable_metrics.pop("elapsed_ms", None)
        stable_metrics.pop("cache_reuse", None)
        return {
            "contract_version": self.CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "edition_digest": edition["content_digest"],
            "registry_digest": digest(registry),
            "catalog_digest": digest(self.media_catalog),
            "videos": selected("video"),
            "podcasts": selected("podcast"),
            "verified_counts": {"videos": 2, "podcasts": 2},
            "decision_metrics": stable_metrics,
        }

    def build_watchlist(self) -> dict[str, Any]:
        started = time.monotonic()
        edition = self._edition()
        registry = self.watch_registry
        catalog = {x["topic_id"]: x for x in self.watch_catalog["topics"]}
        initial = {
            "schema_version": self.CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "checked_sources": [],
            "source_evidence_digests": {},
            "metrics": {
                "source_checks": 0,
                "topic_checks": 0,
                "changed_topics": 0,
                "cache_reuse": 0,
                "elapsed_ms": 0,
            },
        }
        state = self._load_state("watchlist", initial)
        checked = set(state["checked_sources"])
        for source in sorted(registry["sources"], key=lambda s: (int(s["priority"]), s["source_id"])):
            source_id = source["source_id"]
            if source_id in checked:
                state["metrics"]["cache_reuse"] += 1
                continue
            self._maybe_fail("watchlist_source", source_id, "watchlist", state)
            topics = []
            for topic_id in source["topic_ids"]:
                state["metrics"]["topic_checks"] += 1
                topic = deepcopy(catalog[topic_id])
                if date.fromisoformat(topic["first_seen"]) <= date.fromisoformat(self.edition_date):
                    topics.append(topic)
            packet_data = {
                "packet_version": self.CONTRACT_VERSION,
                "edition_date": self.edition_date,
                "source_id": source_id,
                "topics": sorted(topics, key=lambda x: x["topic_id"]),
                "provenance": {"registry_version": registry["schema_version"]},
            }
            packet = self._packet("watchlist-evidence", source_id, packet_data, state["metrics"])
            state["source_evidence_digests"][source_id] = packet["content_digest"]
            checked.add(source_id)
            state["checked_sources"] = sorted(checked)
            state["metrics"]["source_checks"] += 1
            self._save_state("watchlist", state)

        source_for_topic = {}
        for source in registry["sources"]:
            for topic_id in source["topic_ids"]:
                source_for_topic[topic_id] = source["source_id"]

        buckets = {"new_today": [], "updated_today": [], "carried_forward": []}
        today = date.fromisoformat(self.edition_date)
        for topic_id in sorted(catalog):
            topic = deepcopy(catalog[topic_id])
            first_seen = date.fromisoformat(topic["first_seen"])
            if first_seen > today or not topic.get("active", True):
                continue
            changed = date.fromisoformat(topic["last_changed"])
            source_id = source_for_topic[topic_id]
            item = {
                "topic_id": topic_id,
                "title": topic["title"],
                "summary": topic["summary"],
                "first_seen": topic["first_seen"],
                "last_changed": topic["last_changed"],
                "source_id": source_id,
                "source_evidence_digest": state["source_evidence_digests"][source_id],
                "presentation_order": int(topic.get("presentation_order") or 999999),
                "public_topic": deepcopy(topic.get("public_topic") or {}),
                "qualifying_evidence": deepcopy(topic.get("qualifying_evidence") or []),
            }
            if first_seen == today:
                buckets["new_today"].append(item)
            elif changed == today:
                buckets["updated_today"].append(item)
            else:
                buckets["carried_forward"].append(item)

        state["metrics"]["changed_topics"] = len(buckets["new_today"]) + len(buckets["updated_today"])
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state("watchlist", state)
        self._write_metrics()
        stable_metrics = deepcopy(state["metrics"])
        stable_metrics.pop("elapsed_ms", None)
        stable_metrics.pop("cache_reuse", None)
        return {
            "contract_version": self.CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "edition_digest": edition["content_digest"],
            "registry_digest": digest(registry),
            "catalog_digest": digest(self.watch_catalog),
            "reviewed_at": self.watch_catalog.get("reviewed_at"),
            "baseline_note": self.watch_catalog.get("baseline_note"),
            "review_policy": deepcopy(self.watch_catalog.get("review_policy") or {}),
            "source_checks": deepcopy(self.watch_catalog.get("source_checks") or []),
            "candidate_dispositions": deepcopy(self.watch_catalog.get("candidate_dispositions") or []),
            **buckets,
            "counts": {k: len(v) for k, v in buckets.items()},
            "decision_metrics": stable_metrics,
        }

    def build_book_bridges(self) -> dict[str, Any]:
        started = time.monotonic()
        edition = self._edition()
        mapping = self.bridge_map
        mapping_digest = digest(mapping)
        initial = {
            "schema_version": self.CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "decision_digests": {},
            "metrics": {
                "decisions": 0,
                "bridges": 0,
                "no_bridge": 0,
                "cache_reuse": 0,
                "elapsed_ms": 0,
            },
        }
        state = self._load_state("bridges", initial)
        stories = sorted(edition["data"]["stories"], key=lambda s: int(s["presentation_position"]))
        rules = sorted(mapping["rules"], key=lambda r: (int(r["priority"]), r["rule_id"]))
        for story in stories:
            story_id = story["story_id"]
            if story_id in state["decision_digests"]:
                state["metrics"]["cache_reuse"] += 1
                continue
            self._maybe_fail("bridge_decision", story_id, "bridges", state)
            title = story["title"].lower()
            matched = None
            for rule in rules:
                if all(keyword.lower() in title for keyword in rule["title_keywords"]):
                    matched = rule
                    break
            if matched:
                decision = {
                    "story_id": story_id,
                    "decision": "bridge",
                    "rule_id": matched["rule_id"],
                    "book_id": matched["book_id"],
                    "section": matched["section"],
                    "series_url": mapping["series_url"],
                    "reason": matched["reason"],
                }
                state["metrics"]["bridges"] += 1
            else:
                decision = {
                    "story_id": story_id,
                    "decision": "no_bridge",
                    "rule_id": None,
                    "book_id": None,
                    "section": None,
                    "series_url": None,
                    "reason": "No centralized mapping rule is materially relevant to this story.",
                }
                state["metrics"]["no_bridge"] += 1
            packet_data = {
                "packet_version": self.CONTRACT_VERSION,
                "edition_date": self.edition_date,
                "story_id": story_id,
                "story_title": story["title"],
                "story_evidence_packet_digest": story["evidence_packet_digest"],
                "mapping_digest": mapping_digest,
                "decision": decision,
            }
            packet = self._packet("bridge-evidence", story_id, packet_data, state["metrics"])
            state["decision_digests"][story_id] = packet["content_digest"]
            state["metrics"]["decisions"] += 1
            self._save_state("bridges", state)

        decisions = []
        for story in stories:
            record = self.store.read_json(self.store.run_dir / "bridge-evidence" / f"{story['story_id']}.json")
            decision = deepcopy(record["data"]["decision"])
            decision["evidence_digest"] = record["content_digest"]
            decisions.append(decision)
        if len(decisions) != 6:
            raise BuildError("book bridge decisions must cover all six locked stories")

        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state("bridges", state)
        self._write_metrics()
        stable_metrics = deepcopy(state["metrics"])
        stable_metrics.pop("elapsed_ms", None)
        stable_metrics.pop("cache_reuse", None)
        return {
            "contract_version": self.CONTRACT_VERSION,
            "edition_date": self.edition_date,
            "edition_digest": edition["content_digest"],
            "mapping_version": mapping["schema_version"],
            "mapping_digest": mapping_digest,
            "series_title": mapping["series_title"],
            "decisions": decisions,
            "decision_metrics": stable_metrics,
        }
