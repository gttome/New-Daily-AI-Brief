from __future__ import annotations

import json
import time
from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .store import CanonicalStore, ContractError, digest, semantic_digest, utc_now

AGENTS = "agents_non_technical_people"
APPLIED = "applied_genai_knowledge_workers"
TECHNICAL = "technical_ai_engineering"
CATEGORIES = (AGENTS, APPLIED, TECHNICAL)
ALLOCATION = {AGENTS: 2, APPLIED: 2, TECHNICAL: 2}


class EditorialError(ContractError):
    pass


class EditorialCandidateFailure(EditorialError):
    def __init__(self, candidate_id: str, failure_class: str):
        super().__init__(failure_class)
        self.candidate_id = candidate_id
        self.failure_class = failure_class


@dataclass(frozen=True)
class EditorialFailureInjection:
    candidate_id: str
    failure_class: str = "synthetic_editorial_candidate_failure"


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    scheme = (parts.scheme or "https").lower()
    if scheme == "http":
        scheme = "https"
    host = parts.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    ignored = {"ref", "source", "campaign", "fbclid", "gclid"}
    query = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        lower = key.lower()
        if lower.startswith("utm_") or lower in ignored:
            continue
        query.append((key, value))
    return urlunsplit((scheme, host, path, urlencode(sorted(query)), ""))


def classify_agent_skills(candidate: dict[str, Any]) -> bool:
    tags = {str(x).lower().replace("_", "-") for x in candidate.get("tags", [])}
    if tags & {"agent-skill", "agent-skills", "reusable-skill", "reusable-workflow"}:
        return True
    text = " ".join(str(candidate.get(k, "")) for k in ("title", "summary", "why_it_matters")).lower()
    return (
        "agent" in text
        and any(x in text for x in ("reusable", "repeatable", "template"))
        and any(x in text for x in ("skill", "workflow", "procedure", "tool pattern"))
    )


class DiscoveryEditorialPipeline:
    """Deterministic Iteration 2 discovery/editorial module using durable run records."""

    def __init__(
        self,
        store: CanonicalStore,
        edition_date: str,
        fixture_root: Path | str,
        failure_injection: EditorialFailureInjection | None = None,
    ):
        self.store = store
        self.edition_date = edition_date
        self.fixture_root = Path(fixture_root)
        self.failure_injection = failure_injection
        self._failure_fired = False
        self.registry = _read(self.fixture_root / "source-registry.json")
        self.catalog = _read(self.fixture_root / "source-catalog.json")
        self.novelty = _read(self.fixture_root / "novelty-index.json")
        if self.registry.get("schema_version") != "1.0.0":
            raise EditorialError("unsupported source registry version")
        if self.catalog.get("schema_version") != "1.0.0":
            raise EditorialError("unsupported source catalog version")
        if self.novelty.get("schema_version") != "1.0.0":
            raise EditorialError("unsupported novelty index version")
        self.by_candidate = {x["candidate_id"]: x for x in self.catalog["candidates"]}

    @property
    def state_path(self) -> Path:
        return self.store.run_dir / "discovery-state.json"

    @property
    def metrics_path(self) -> Path:
        return self.store.run_dir / "discovery-metrics.json"

    @property
    def packet_dir(self) -> Path:
        return self.store.run_dir / "evidence-packets"

    def packet_path(self, candidate_id: str) -> Path:
        return self.packet_dir / f"{candidate_id}.json"

    def source_registry_data(self) -> dict[str, Any]:
        return deepcopy(self.registry)

    def novelty_index_data(self) -> dict[str, Any]:
        items = [
            {
                "normalized_url": normalize_url(x["url"]),
                "development_key": x.get("development_key"),
                "published_at": x.get("published_at"),
            }
            for x in self.novelty.get("prior_items", [])
        ]
        items.sort(key=lambda x: (x["normalized_url"], str(x.get("development_key"))))
        return {"schema_version": "1.0.0", "window_days": self.novelty.get("window_days", 30), "items": items}

    def _new_state(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0.0",
            "edition_date": self.edition_date,
            "scan_complete": False,
            "eligible": {c: [] for c in CATEGORIES},
            "rejections": {},
            "fallback_tier_by_category": {c: 0 for c in CATEGORIES},
            "packet_digests": {},
            "metrics": {
                "source_scans": 0,
                "metadata_attempts": 0,
                "metadata_failures": 0,
                "metadata_retries": 0,
                "candidates_seen": 0,
                "freshness_rejections": 0,
                "novelty_rejections": 0,
                "deep_retrieval_count": 0,
                "evidence_packet_cache_hits": 0,
                "evidence_packet_cache_misses": 0,
                "fallback_expansions": {c: [] for c in CATEGORIES},
                "fallback_sources_used": [],
                "due_source_ids": [],
                "skipped_not_due_source_ids": [],
                "elapsed_ms": 0,
            },
        }

    def _load_state(self) -> dict[str, Any]:
        return self.store.read_json(self.state_path) or self._new_state()

    def _save_state(self, state: dict[str, Any]) -> None:
        self.store._atomic_write(self.state_path, state)

    def _is_due(self, source: dict[str, Any]) -> bool:
        last = source.get("last_checked")
        if not last:
            return True
        return (date.fromisoformat(self.edition_date) - date.fromisoformat(last)).days >= int(source.get("cadence_days", 1))

    def _fresh(self, published_at: str) -> bool:
        age = (date.fromisoformat(self.edition_date) - date.fromisoformat(published_at[:10])).days
        return 0 <= age <= int(self.registry["policy"]["freshness_days"])

    def _feasible(self, category: str, ids: list[str]) -> bool:
        if category != AGENTS:
            return len(ids) >= 2
        values = [self.by_candidate[x] for x in ids]
        return any(classify_agent_skills(x) for x in values) and any(not classify_agent_skills(x) for x in values)

    def _scan_source(self, source: dict[str, Any], state: dict[str, Any]) -> None:
        m = state["metrics"]
        m["source_scans"] += 1
        failures_left = int(source.get("synthetic_metadata_failures", 0))
        max_attempts = int(self.registry["policy"]["max_metadata_attempts"])
        success = False
        for attempt in range(1, max_attempts + 1):
            m["metadata_attempts"] += 1
            if attempt <= failures_left:
                m["metadata_failures"] += 1
                if attempt < max_attempts:
                    m["metadata_retries"] += 1
                continue
            success = True
            break
        if not success:
            return
        prior_urls = {x["normalized_url"] for x in self.novelty_index_data()["items"]}
        category = source["category_id"]
        for candidate_id in source.get("candidate_ids", []):
            candidate = deepcopy(self.by_candidate[candidate_id])
            m["candidates_seen"] += 1
            if not self._fresh(candidate["published_at"]):
                state["rejections"][candidate_id] = "freshness"
                m["freshness_rejections"] += 1
                continue
            candidate["normalized_url"] = normalize_url(candidate["url"])
            if candidate["normalized_url"] in prior_urls:
                state["rejections"][candidate_id] = "novelty_url_collision"
                m["novelty_rejections"] += 1
                continue
            state["eligible"][category].append(candidate_id)

    def _scan_metadata(self, state: dict[str, Any]) -> None:
        if state["scan_complete"]:
            return
        sources = sorted(
            [x for x in self.registry["sources"] if x.get("enabled", True)],
            key=lambda x: (int(x["fallback_tier"]), int(x["priority"]), x["source_id"]),
        )
        due = [x for x in sources if self._is_due(x)]
        state["metrics"]["due_source_ids"] = [x["source_id"] for x in due]
        state["metrics"]["skipped_not_due_source_ids"] = [x["source_id"] for x in sources if x not in due]
        max_tier = int(self.registry["policy"]["max_fallback_tier"])
        for category in CATEGORIES:
            for tier in range(max_tier + 1):
                tier_sources = [x for x in due if x["category_id"] == category and int(x["fallback_tier"]) == tier]
                for source in tier_sources:
                    self._scan_source(source, state)
                    if tier > 0:
                        state["metrics"]["fallback_sources_used"].append(source["source_id"])
                ids = self._sorted_eligible(category, state)
                if self._feasible(category, ids):
                    state["fallback_tier_by_category"][category] = tier
                    break
                if tier < max_tier:
                    state["metrics"]["fallback_expansions"][category].append(tier + 1)
            if not self._feasible(category, self._sorted_eligible(category, state)):
                raise EditorialError(f"candidate shortage after bounded fallback: {category}")
        state["scan_complete"] = True
        self._save_state(state)

    def _sorted_eligible(self, category: str, state: dict[str, Any]) -> list[str]:
        return sorted(
            state["eligible"][category],
            key=lambda cid: (-int(self.by_candidate[cid]["quality_score"]), cid),
        )

    def _selected_ids(self, state: dict[str, Any]) -> list[str]:
        selected: list[str] = []
        for category in CATEGORIES:
            ids = self._sorted_eligible(category, state)
            if category == AGENTS:
                skill = next(x for x in ids if classify_agent_skills(self.by_candidate[x]))
                ordinary = next(x for x in ids if not classify_agent_skills(self.by_candidate[x]))
                selected.extend([skill, ordinary])
            else:
                selected.extend(ids[:2])
        return selected

    def _packet_data(self, candidate_id: str) -> dict[str, Any]:
        c = self.by_candidate[candidate_id]
        return {
            "packet_version": "1.0.0",
            "candidate_id": candidate_id,
            "category_id": c["category_id"],
            "title": c["title"],
            "published_at": c["published_at"],
            "normalized_url": normalize_url(c["url"]),
            "development_key": c["development_key"],
            "quality_score": c["quality_score"],
            "agent_skills": classify_agent_skills(c),
            "provenance": {
                "source_id": c["source_id"],
                "canonical_url": c["url"],
                "claims": deepcopy(c.get("deep_evidence", {}).get("claims", [])),
            },
        }

    def _packet(self, candidate_id: str, state: dict[str, Any]) -> dict[str, Any]:
        path = self.packet_path(candidate_id)
        data = self._packet_data(candidate_id)
        expected = digest(data)
        existing = self.store.read_json(path)
        if existing and existing.get("status") == "locked" and existing.get("content_digest") == expected:
            state["metrics"]["evidence_packet_cache_hits"] += 1
            state["packet_digests"][candidate_id] = expected
            self._save_state(state)
            return existing
        if self.failure_injection and not self._failure_fired and self.failure_injection.candidate_id == candidate_id:
            self._failure_fired = True
            self._save_state(state)
            raise EditorialCandidateFailure(candidate_id, self.failure_injection.failure_class)
        state["metrics"]["deep_retrieval_count"] += 1
        if state["metrics"]["deep_retrieval_count"] > int(self.registry["policy"]["deep_retrieval_limit"]):
            raise EditorialError("deep retrieval limit exceeded")
        state["metrics"]["evidence_packet_cache_misses"] += 1
        record = {
            "schema_version": "1.0.0",
            "candidate_id": candidate_id,
            "status": "locked",
            "content_digest": expected,
            "data": data,
            "locked_at": utc_now(),
        }
        self.packet_dir.mkdir(parents=True, exist_ok=True)
        self.store._atomic_write(path, record)
        state["packet_digests"][candidate_id] = expected
        self._save_state(state)
        return record

    def discover(self) -> dict[str, Any]:
        started = time.monotonic()
        state = self._load_state()
        self._scan_metadata(state)
        selected = self._selected_ids(state)
        for candidate_id in selected:
            self._packet(candidate_id, state)
        stable_metrics = {
            k: deepcopy(v)
            for k, v in state["metrics"].items()
            if k not in {"elapsed_ms", "evidence_packet_cache_hits", "evidence_packet_cache_misses"}
        }
        result = {
            "contract_version": "1.0.0",
            "registry_digest": digest(self.source_registry_data()),
            "novelty_digest": digest(self.novelty_index_data()),
            "selected_candidate_ids": selected,
            "selected_evidence_packet_digests": {x: state["packet_digests"][x] for x in selected},
            "rejections": dict(sorted(state["rejections"].items())),
            "fallback_tier_by_category": deepcopy(state["fallback_tier_by_category"]),
            "decision_metrics": stable_metrics,
        }
        state["metrics"]["elapsed_ms"] = max(0, int((time.monotonic() - started) * 1000))
        self._save_state(state)
        telemetry = deepcopy(state["metrics"])
        telemetry["recorded_at"] = utc_now()
        self.store._atomic_write(self.metrics_path, telemetry)
        return result

    def build_edition(self) -> dict[str, Any]:
        discovery = self.store.load_artifact("discovery")
        if not discovery or discovery.get("status") != "locked":
            raise EditorialError("discovery must be locked before editorial selection")
        stories = []
        for position, candidate_id in enumerate(discovery["data"]["selected_candidate_ids"], start=1):
            packet = self.store.read_json(self.packet_path(candidate_id))
            if not packet or packet.get("status") != "locked":
                raise EditorialError(f"missing locked evidence packet: {candidate_id}")
            data = packet["data"]
            stories.append({
                "story_id": candidate_id,
                "category_id": data["category_id"],
                "title": data["title"],
                "source_id": data["provenance"]["source_id"],
                "url": data["provenance"]["canonical_url"],
                "published_at": data["published_at"],
                "agent_skills": data["agent_skills"],
                "evidence_packet_digest": packet["content_digest"],
                "presentation_position": position,
            })
        counts = {c: sum(x["category_id"] == c for x in stories) for c in CATEGORIES}
        if counts != ALLOCATION or sum(bool(x["agent_skills"]) for x in stories) != 1:
            raise EditorialError("editorial allocation invariant failed")
        return {
            "editorial_contract_version": "1.0.0",
            "stories": stories,
            "allocation": {"agents": 2, "applied": 2, "technical": 2},
            "category_counts": counts,
            "agent_skills_count": 1,
            "presentation_order": list(CATEGORIES),
            "discovery_digest": discovery["content_digest"],
        }
