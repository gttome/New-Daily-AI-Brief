#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

AGENTS = "agents_non_technical_people"
APPLIED = "applied_genai_knowledge_workers"
TECHNICAL = "technical_ai_engineering"
CATEGORIES = (AGENTS, APPLIED, TECHNICAL)


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"required input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean_text(value: Any, limit: int = 700) -> str:
    text = html.unescape(str(value or ""))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:")
    return cut + "…"


def normalize_url(url: str) -> str:
    p = urlsplit(url.strip())
    scheme = "https" if p.scheme in {"", "http"} else p.scheme.lower()
    host = p.netloc.lower()
    if host.startswith("www."):
        host = host[4:]
    path = p.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, host, path, "", ""))


def stable_id(url: str) -> str:
    return "live-" + hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()[:16]


def why_it_matters(focus: str, evidence: str) -> str:
    sentence = clean_text(evidence, 360)
    if focus == TECHNICAL:
        prefix = "For AI engineering teams, the practical significance is that "
    elif focus == APPLIED:
        prefix = "For knowledge workers and enterprise teams, the practical significance is that "
    else:
        prefix = "For people using or designing agents without deep engineering work, the practical significance is that "
    if not sentence:
        return prefix + "the development changes how this capability can be applied or governed in real workflows."
    sentence = sentence[0].lower() + sentence[1:] if len(sentence) > 1 else sentence.lower()
    return prefix + sentence.rstrip(".") + "."


def prior_items(legacy_root: Path, edition_date: str, window_days: int = 30) -> list[dict[str, Any]]:
    root = legacy_root / "_data" / "editions"
    if not root.exists():
        return []
    target = date.fromisoformat(edition_date)
    minimum = target - timedelta(days=window_days)
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in sorted(root.glob("*.json")):
        try:
            day = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if not (minimum <= day < target):
            continue
        data = load(path)
        for story in data.get("stories", []):
            source = story.get("source") or {}
            url = source.get("normalized_url") or source.get("url")
            if not url:
                continue
            normalized = normalize_url(str(url))
            if normalized in seen:
                continue
            seen.add(normalized)
            items.append({
                "url": normalized,
                "development_key": story.get("story_id") or normalized,
                "published_at": source.get("publication_date") or story.get("event_date") or path.stem,
            })
    return items


def select_candidates(metadata: dict[str, Any], evidence: dict[str, Any]) -> list[dict[str, Any]]:
    if metadata.get("profile_id") != "under80-v1":
        raise SystemExit("unsupported live metadata profile")
    if metadata.get("coverage_ready") is not True:
        raise SystemExit("live discovery did not achieve required 3/3/3 coverage")
    rows = metadata.get("candidates")
    if not isinstance(rows, list) or not rows:
        raise SystemExit("live metadata candidate set is empty")

    evidence_rows = {
        row["candidate_id"]: row
        for row in evidence.get("model_visible", [])
        if isinstance(row, dict) and row.get("candidate_id")
    }
    available = [
        row for row in rows
        if row.get("candidate_id") in evidence_rows
        and evidence_rows[row["candidate_id"]].get("excerpt")
    ]
    by_focus = {
        focus: sorted(
            [row for row in available if row.get("focus_hint") == focus and row.get("background_only") is not True],
            key=lambda x: (-int(x.get("prefilter_score") or 0), str(x.get("candidate_id"))),
        )
        for focus in CATEGORIES
    }

    preferred = metadata.get("preferred_agent_skill_candidate_id")
    agent_skill = next(
        (
            row for row in by_focus[AGENTS]
            if row.get("candidate_id") == preferred and row.get("agent_skill_story_ready") is True
        ),
        None,
    )
    if agent_skill is None:
        agent_skill = next((row for row in by_focus[AGENTS] if row.get("agent_skill_story_ready") is True), None)
    ordinary_agent = next(
        (
            row for row in by_focus[AGENTS]
            if row.get("candidate_id") != (agent_skill or {}).get("candidate_id")
            and row.get("agent_skill_signal") is not True
        ),
        None,
    )
    if agent_skill is None or ordinary_agent is None:
        raise SystemExit("live candidates do not contain one Agent Skills story plus one ordinary agent story")

    selected = [agent_skill, ordinary_agent]
    for focus in (APPLIED, TECHNICAL):
        if len(by_focus[focus]) < 2:
            raise SystemExit(f"live candidate shortage for {focus}")
        selected.extend(by_focus[focus][:2])

    if len(selected) != 6:
        raise SystemExit("exactly six live stories were not selected")
    if sum(bool(x.get("agent_skill_story_ready")) for x in selected) != 1:
        raise SystemExit("selected live edition must contain exactly one Agent Skills story")
    return selected


def build_editorial_inputs(
    edition_date: str,
    metadata: dict[str, Any],
    evidence: dict[str, Any],
    legacy_root: Path,
    output_root: Path,
) -> dict[str, Any]:
    selected = select_candidates(metadata, evidence)
    selected_candidate_ids = {row["candidate_id"] for row in selected}
    evidence_by_id = {x["candidate_id"]: x for x in evidence.get("model_visible", [])}
    available = [
        row for row in metadata.get("candidates", [])
        if row.get("candidate_id") in evidence_by_id
        and evidence_by_id[row["candidate_id"]].get("excerpt")
        and row.get("background_only") is not True
    ]
    registry_sources = []
    catalog_candidates = []
    selected_manifest = []

    for focus in CATEGORIES:
        members = sorted(
            [row for row in available if row.get("focus_hint") == focus],
            key=lambda row: (-int(row.get("prefilter_score") or 0), str(row.get("candidate_id"))),
        )
        if len(members) < 3:
            raise SystemExit(f"live canonical candidate pool requires at least three evidenced candidates for {focus}")
        source_id = f"live-{focus}"
        ids: list[str] = []
        for row in members:
            ev = evidence_by_id[row["candidate_id"]]
            canonical = normalize_url(row["canonical_url"])
            sid = stable_id(canonical)
            ids.append(sid)
            excerpt = clean_text(ev.get("excerpt") or row.get("snippet"), 650)
            summary = clean_text(row.get("snippet") or excerpt, 420)
            if not summary:
                summary = clean_text(excerpt, 420)
            skill = bool(row.get("agent_skill_story_ready"))
            tags = ["live-discovery", focus.replace("_", "-")]
            if skill:
                tags.append("agent-skill")
            catalog_candidates.append({
                "candidate_id": sid,
                "source_id": source_id,
                "category_id": focus,
                "title": clean_text(row.get("headline"), 220),
                "url": canonical,
                "published_at": str(row.get("published_at") or row.get("metadata_event_at"))[:10],
                "published_at_full": str(row.get("published_at") or row.get("metadata_event_at")),
                "metadata_event_at": str(row.get("metadata_event_at") or row.get("published_at")),
                "publisher": row.get("publisher"),
                "source_reliability": row.get("source_reliability"),
                "source_word_count": int(ev.get("source_word_count") or 0),
                "evidence_excerpt": excerpt,
                "agent_skills": skill,
                "summary": summary,
                "why_it_matters": why_it_matters(focus, excerpt),
                "quality_score": int(row.get("prefilter_score") or 0),
                "development_key": canonical,
                "tags": tags,
                "deep_evidence": {
                    "claims": [{
                        "claim": excerpt,
                        "source_url": canonical,
                        "source_reliability": row.get("source_reliability"),
                        "publisher": row.get("publisher"),
                    }]
                },
            })
            if row["candidate_id"] in selected_candidate_ids:
                selected_manifest.append({
                    "story_id": sid,
                    "candidate_id": row["candidate_id"],
                    "focus": focus,
                    "headline": clean_text(row.get("headline"), 220),
                    "url": canonical,
                    "published_at": str(row.get("published_at") or row.get("metadata_event_at")),
                    "agent_skills": skill,
                    "source_reliability": row.get("source_reliability"),
                    "prefilter_score": int(row.get("prefilter_score") or 0),
                })
        registry_sources.append({
            "source_id": source_id,
            "category_id": focus,
            "fallback_tier": 0,
            "priority": 10,
            "cadence_days": 1,
            "last_checked": None,
            "enabled": True,
            "synthetic_metadata_failures": 0,
            "candidate_ids": ids,
        })

    editor = output_root / "editorial"
    dump(editor / "source-registry.json", {
        "schema_version": "1.0.0",
        "policy": {
            "freshness_days": 30,
            "max_metadata_attempts": 1,
            "max_fallback_tier": 0,
            "deep_retrieval_limit": 6,
        },
        "sources": registry_sources,
    })
    dump(editor / "source-catalog.json", {
        "schema_version": "1.0.0",
        "candidates": catalog_candidates,
    })
    dump(editor / "novelty-index.json", {
        "schema_version": "1.0.0",
        "window_days": 30,
        "prior_items": prior_items(legacy_root, edition_date, 30),
    })

    manifest = {
        "schema_version": "1.0.0",
        "edition_date": edition_date,
        "input_mode": "live_zero_incremental_cost_editorial",
        "discovery_profile": metadata.get("profile_id"),
        "metadata_cutoff": metadata.get("cutoff"),
        "selected_story_count": len(selected_manifest),
        "selected_stories": selected_manifest,
        "canonical_entry_point": "start_daily_brief(date, mode)",
        "canonical_mode": "production",
        "run_depth": "editorial_locked",
        "publication_attempted": False,
        "image_generation_attempted": False,
        "media_generation_attempted": False,
        "fail_closed_note": (
            "Live editorial discovery is complete. Media, professional image generation, "
            "reader publication, and ChatGPT Site synchronization are separate gated stages "
            "and are not fabricated by this zero-incremental-cost adapter."
        ),
    }
    dump(output_root / "live-input-manifest.json", manifest)
    return manifest


def write_draft(output_root: Path, manifest: dict[str, Any], catalog: dict[str, Any]) -> None:
    by_id = {x["candidate_id"]: x for x in catalog["candidates"]}
    lines = [
        f"# Daily Generative AI Brief — {manifest['edition_date']} — Live Editorial Draft",
        "",
        "> Canonical greenfield editorial selection. Media, final professional images, publication, and Site synchronization have not yet been attempted.",
        "",
    ]
    for idx, item in enumerate(manifest["selected_stories"], start=1):
        c = by_id[item["story_id"]]
        lines.extend([
            f"## {idx}. {c['title']}",
            "",
            c["summary"],
            "",
            f"**Why it matters:** {c['why_it_matters']}",
            "",
            f"**Source:** {c['url']}",
            "",
        ])
    (output_root / "live-editorial-draft.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Convert bounded live discovery evidence into canonical greenfield editorial inputs")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--metadata-json", required=True)
    ap.add_argument("--evidence-json", required=True)
    ap.add_argument("--evidence-receipt-json", required=True)
    ap.add_argument("--legacy-root", default="legacy_snapshot")
    ap.add_argument("--output-root", required=True)
    args = ap.parse_args()

    edition_date = args.edition_date
    try:
        date.fromisoformat(edition_date)
    except ValueError as exc:
        raise SystemExit("edition date must be YYYY-MM-DD") from exc

    metadata = load(Path(args.metadata_json))
    evidence = load(Path(args.evidence_json))
    receipt = load(Path(args.evidence_receipt_json))
    if receipt.get("ready") is not True:
        raise SystemExit("live article evidence preflight is not ready")
    if int(receipt.get("retrieved") or 0) != 9:
        raise SystemExit("live article evidence must contain nine successful deep reviews")
    focus_counts = receipt.get("focus_counts") or {}
    if any(int(focus_counts.get(focus) or 0) != 3 for focus in CATEGORIES):
        raise SystemExit("live article evidence must contain exactly three deep reviews per focus")

    output_root = Path(args.output_root)
    manifest = build_editorial_inputs(
        edition_date,
        metadata,
        evidence,
        Path(args.legacy_root),
        output_root,
    )
    catalog = load(output_root / "editorial" / "source-catalog.json")
    write_draft(output_root, manifest, catalog)
    print(json.dumps({
        "edition_date": edition_date,
        "selected_story_count": manifest["selected_story_count"],
        "run_depth": manifest["run_depth"],
        "output_root": str(output_root),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
