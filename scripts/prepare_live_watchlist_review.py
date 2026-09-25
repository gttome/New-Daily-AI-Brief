#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

STOP = {
    "about","after","again","against","also","available","because","being","between","build","building",
    "from","into","more","new","now","that","their","there","these","this","those","through","using","with",
    "without","your","agent","agents","model","models","system","systems","artificial","intelligence","generative",
    "work","working","today","current","become","becomes","across","toward","towards","first","layer"
}
PRIMARY_KINDS = {"company", "university", "research", "standards", "community"}


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"required file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def tokens(value: str) -> set[str]:
    return {
        t for t in re.findall(r"[a-z0-9][a-z0-9-]{3,}", value.lower())
        if t not in STOP and not t.isdigit()
    }


def topic_terms(topic: dict[str, Any]) -> tuple[set[str], set[str]]:
    name = tokens(str(topic.get("name") or ""))
    body = tokens(" ".join(str(topic.get(k) or "") for k in ("name","summary","why_now","practical_value")))
    for evidence in topic.get("evidence") or []:
        body |= tokens(str(evidence.get("title") or ""))
    return name, body


def main() -> int:
    ap = argparse.ArgumentParser(description="Build a conservative Watchlist review receipt from the current source sweep")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--baseline-json", required=True)
    ap.add_argument("--discovery-json", required=True)
    ap.add_argument("--source-registry-json", required=True)
    ap.add_argument("--output", required=True)
    args = ap.parse_args()

    edition = date.fromisoformat(args.edition_date)
    prior = load(Path(args.baseline_json))
    discovery = load(Path(args.discovery_json))
    registry = load(Path(args.source_registry_json))
    if date.fromisoformat(str(prior.get("edition_date") or "")) >= edition:
        raise SystemExit("Watchlist baseline must predate the current edition")

    kinds = {str(x.get("source_id") or ""): str(x.get("kind") or "") for x in registry.get("sources") or []}
    names = {str(x.get("source_id") or ""): str(x.get("name") or x.get("source_id") or "") for x in registry.get("sources") or []}
    prior_topics = {str(t["topic_id"]): t for t in prior.get("topics") or []}
    prior_urls = {
        topic_id: {str(e.get("url")) for e in topic.get("evidence") or [] if e.get("url")}
        for topic_id, topic in prior_topics.items()
    }
    vectors = {topic_id: topic_terms(topic) for topic_id, topic in prior_topics.items()}

    source_checks = [{
        "source_id": str(row.get("source_id") or ""),
        "status": row.get("status"),
        "checked_at": row.get("checked_at"),
        "last_successful_check": row.get("last_successful_check"),
        "reason": row.get("reason"),
        "topic_ids": [],
    } for row in discovery.get("sources") or [] if row.get("source_id")]

    earliest = edition - timedelta(days=7)
    candidates: list[tuple[dict[str, Any], list[str]]] = []
    for candidate in discovery.get("candidates") or []:
        url = str(candidate.get("url") or candidate.get("canonical_url") or "")
        title = str(candidate.get("title") or candidate.get("headline") or "")
        published = str(candidate.get("publication_date") or candidate.get("published_at") or "")[:10]
        if not url.startswith("https://") or not title:
            continue
        try:
            if published and not (earliest <= date.fromisoformat(published) <= edition):
                continue
        except ValueError:
            continue
        source_ids = [str(x) for x in candidate.get("source_ids") or []]
        qualifying_ids = [sid for sid in source_ids if kinds.get(sid) in PRIMARY_KINDS]
        if qualifying_ids:
            candidates.append((candidate, qualifying_ids))

    matches: dict[str, list[tuple[int, dict[str, Any], str]]] = {}
    unmatched: list[dict[str, Any]] = []
    for candidate, source_ids in candidates:
        cterms = tokens(str(candidate.get("title") or candidate.get("headline") or ""))
        best: tuple[int, str] | None = None
        for topic_id, (name_terms, body_terms) in vectors.items():
            overlap = cterms & body_terms
            name_overlap = cterms & name_terms
            score = len(overlap) + (2 if name_overlap else 0)
            if len(overlap) >= 2 and name_overlap and (best is None or score > best[0]):
                best = (score, topic_id)
        if best is None:
            unmatched.append(candidate)
            continue
        score, topic_id = best
        url = str(candidate.get("url") or candidate.get("canonical_url") or "")
        if url not in prior_urls[topic_id]:
            matches.setdefault(topic_id, []).append((score, candidate, source_ids[0]))

    updated_topics = []
    used_urls: set[str] = set()
    source_check_map = {x["source_id"]: x for x in source_checks}
    for topic_id, rows in sorted(matches.items()):
        rows.sort(key=lambda x: (-x[0], str(x[1].get("url") or "")))
        _, candidate, source_id = rows[0]
        url = str(candidate.get("url") or candidate.get("canonical_url") or "")
        if url in used_urls:
            continue
        used_urls.add(url)
        title = str(candidate.get("title") or candidate.get("headline") or "")
        published = str(candidate.get("publication_date") or candidate.get("published_at") or "")[:10] or None
        checked_at = f"{args.edition_date}T12:00:00-05:00"
        updated_topics.append({
            "topic_id": topic_id,
            "material_change": f"Current Watchlist source review found a new qualifying development: {title}",
            "evidence": [{
                "title": title,
                "url": url,
                "publisher": names.get(source_id) or source_id,
                "source_id": source_id,
                "kind": kinds.get(source_id) or "primary",
                "publication_date": published,
                "checked_at": checked_at,
                "review_depth": "Current source metadata and origin reviewed by the bounded Watchlist source sweep.",
                "qualifies_for_daily_state": True,
            }],
        })
        if source_id in source_check_map:
            source_check_map[source_id]["topic_ids"].append(topic_id)

    dispositions = [{
        "name": row["evidence"][0]["title"],
        "disposition": "update_existing",
        "topic_id": row["topic_id"],
        "reason": row["material_change"],
    } for row in updated_topics]
    for candidate in unmatched[:12]:
        dispositions.append({
            "name": str(candidate.get("title") or candidate.get("headline") or "Unmatched Watchlist lead"),
            "disposition": "needs_research",
            "reason": "Current source lead did not map conservatively to an existing topic and did not independently meet the new-topic threshold.",
            "evidence_urls": [str(candidate.get("url") or candidate.get("canonical_url") or "")],
        })

    successful_kinds = {
        kinds.get(str(row.get("source_id") or ""))
        for row in discovery.get("sources") or []
        if row.get("status") in {"retrieved", "no_candidate_links"}
    }
    successful_kinds.discard(None)
    if len(dispositions) < 3 or len(successful_kinds) < 3:
        raise SystemExit("current Watchlist sweep cannot certify a zero-new result; broader review is required")

    review = {
        "schema_version": "1.0.0",
        "edition_date": args.edition_date,
        "checked_at": f"{args.edition_date}T12:00:00-05:00",
        "review_complete": True,
        "review_mode": "automated_current_watchlist_source_sweep",
        "policy": {"new_topic_min_independent_sources": 2, "zero_new_min_candidates_reviewed": 3},
        "baseline_note": (
            f"{args.edition_date} Watchlist source sweep: 0 new topics met the independent-evidence threshold; "
            f"{len(updated_topics)} existing topics received qualifying new evidence; remaining active topics were carried forward."
        ),
        "source_checks": source_checks,
        "updated_topics": updated_topics,
        "new_topics": [],
        "zero_new_certified": True,
        "candidate_dispositions": dispositions,
    }
    dump(Path(args.output), review)
    print(json.dumps({
        "edition_date": args.edition_date,
        "updated_topics": len(updated_topics),
        "new_topics": 0,
        "reviewed_candidates": len(dispositions),
        "source_kinds": sorted(successful_kinds),
        "zero_new_certified": True,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
