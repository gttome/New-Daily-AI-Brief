#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

AGENTS = "agents_non_technical_people"
APPLIED = "applied_genai_knowledge_workers"
TECHNICAL = "technical_ai_engineering"
STOP = {
    "about","after","again","against","available","brings","from","into","more","new","now",
    "that","their","there","these","this","those","through","using","with","without","your",
    "adds","targets","inside","gives","makes"
}


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"required input missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def words(text: str) -> set[str]:
    return {
        x for x in re.findall(r"[a-z0-9][a-z0-9-]{3,}", text.lower())
        if x not in STOP
    }


def story_text(candidate: dict[str, Any]) -> str:
    return " ".join(str(candidate.get(k, "")) for k in ("title", "summary", "why_it_matters"))


def safe_id(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:80] or "item"


def prepare_media(media: dict[str, Any], out: Path) -> dict[str, Any]:
    if media.get("ready") is not True:
        raise SystemExit("live media discovery is not ready")
    selected = media.get("selected") or {}
    videos = selected.get("videos") or []
    podcasts = selected.get("podcasts") or []
    if len(videos) != 2 or len(podcasts) != 2:
        raise SystemExit("exactly two verified videos and two verified podcasts are required")

    items: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for kind, rows in (("video", videos), ("podcast", podcasts)):
        for idx, row in enumerate(rows, start=1):
            media_id = f"live-{kind}-{idx}-{safe_id(row.get('source_id') or row.get('title') or str(idx))}"
            duration_seconds = row.get("runtime_seconds")
            duration_minutes = None if duration_seconds is None else max(1, int(round(int(duration_seconds) / 60)))
            items.append({
                "media_id": media_id,
                "kind": kind,
                "title": row["title"],
                "url": row["url"],
                "published_at": row.get("publication_date") or str(row.get("published_at", ""))[:10],
                "duration_minutes": duration_minutes,
                "available": bool(row.get("available", True)),
                "synthetic_verification_failures": 0,
                "live_provenance": {
                    "source_id": row.get("source_id"),
                    "published_at": row.get("published_at"),
                    "runtime_seconds": row.get("runtime_seconds"),
                    "freshness_tier": row.get("freshness_tier"),
                    "score": row.get("score"),
                },
            })
            sources.append({
                "source_id": f"live-{kind}-source-{idx}",
                "kind": kind,
                "fallback_tier": 0,
                "priority": idx * 10,
                "enabled": True,
                "candidate_ids": [media_id],
            })

    dump(out / "media-registry.json", {
        "schema_version": "1.0.0",
        "policy": {
            "max_verification_attempts": 1,
            "max_candidate_checks_per_kind": 4,
            "max_fallback_tier": 0,
        },
        "sources": sources,
    })
    dump(out / "media-catalog.json", {"schema_version": "1.0.0", "items": items})
    return {"videos": videos, "podcasts": podcasts, "catalog_items": items}


def prepare_watchlist(edition_date: str, editorial: dict[str, Any], legacy_root: Path, out: Path) -> dict[str, Any]:
    source = load(legacy_root / "_data" / "watchlist.json")
    candidates = editorial.get("candidates") or []
    story_terms = set().union(*(words(story_text(x)) for x in candidates)) if candidates else set()
    topics = []
    updated_ids: list[str] = []
    new_ids: list[str] = []

    for topic in source.get("topics", []):
        first_raw = str(topic.get("first_detected") or topic.get("first_seen") or edition_date)
        changed_raw = str(topic.get("updated_at") or topic.get("last_changed") or first_raw)
        first_seen = first_raw[:10]
        last_changed = changed_raw[:10]
        topic_terms = words(" ".join(str(topic.get(k, "")) for k in ("name", "summary", "why_now", "practical_value")))
        overlap = sorted(story_terms & topic_terms)
        strong_overlap = len(overlap) >= 2 or any(
            term in overlap for term in ("skills", "agentic", "observability", "evaluation", "governance", "context", "inference", "model")
        )
        if strong_overlap and last_changed < edition_date:
            last_changed = edition_date
            updated_ids.append(topic["topic_id"])
        if first_seen == edition_date:
            new_ids.append(topic["topic_id"])
        topics.append({
            "topic_id": topic["topic_id"],
            "title": topic.get("name") or topic["topic_id"],
            "summary": topic.get("summary") or topic.get("why_now") or "Carried forward from the verified Emerging AI Watchlist.",
            "first_seen": first_seen,
            "last_changed": last_changed,
            "active": topic.get("status") not in {"retired", "inactive"},
            "live_overlap_terms": overlap[:12],
        })

    if not topics:
        raise SystemExit("legacy Watchlist contains no topics to carry forward")
    dump(out / "watchlist-registry.json", {
        "schema_version": "1.0.0",
        "sources": [{
            "source_id": "verified-watchlist-carry-forward",
            "priority": 10,
            "topic_ids": [x["topic_id"] for x in topics],
        }],
    })
    dump(out / "watchlist-catalog.json", {"schema_version": "1.0.0", "topics": topics})
    return {
        "source_edition_date": source.get("edition_date"),
        "topic_count": len(topics),
        "new_today": new_ids,
        "updated_today": updated_ids,
        "carried_forward": [x["topic_id"] for x in topics if x["topic_id"] not in set(new_ids + updated_ids)],
        "method": "verified_prior_watchlist_plus_conservative_story_overlap_updates",
        "new_topic_creation": "disabled_without_independent_multi-source_threshold_evidence",
    }


def bridge_rule(candidate: dict[str, Any], index: int) -> dict[str, Any] | None:
    text = story_text(candidate).lower()
    title_tokens = [x for x in re.findall(r"[a-z0-9][a-z0-9-]{3,}", candidate.get("title", "").lower()) if x not in STOP]
    def keywords(preferred: tuple[str, ...]) -> list[str]:
        hit = [x for x in preferred if x in text and x in title_tokens]
        if hit:
            return hit[:2]
        return title_tokens[:2]

    if any(x in text for x in ("skill", "context", "instruction", "retrieval", "grounding")):
        return {
            "rule_id": f"live-bridge-{index}-context",
            "priority": index * 10,
            "title_keywords": keywords(("skills", "skill", "context", "grounding", "retrieval", "instructions")),
            "book_id": "Reliable Generative AI Context Engineering",
            "section": "Chapter 3 — Designing High-Quality Contexts",
            "reason": "The story materially concerns reusable instructions, evidence, or context quality.",
        }
    if any(x in text for x in ("evaluation", "benchmark", "verify", "verification", "observability", "provenance")):
        return {
            "rule_id": f"live-bridge-{index}-verification",
            "priority": index * 10,
            "title_keywords": keywords(("evaluation", "benchmark", "observability", "verification", "provenance")),
            "book_id": "Reliable Generative AI",
            "section": "Chapter 3, section 3.3.3 — Verification as the Final Gate",
            "reason": "The story materially concerns verification, evaluation, or operational evidence.",
        }
    if any(x in text for x in ("security", "privacy", "approval", "autonomy", "confidential", "governance", "trust")):
        return {
            "rule_id": f"live-bridge-{index}-trust",
            "priority": index * 10,
            "title_keywords": keywords(("security", "privacy", "approval", "confidential", "governance", "trust")),
            "book_id": "Reliable Generative AI",
            "section": "Chapter 4, section 4.1.2 — Managing Expectations and Calibrating Trust",
            "reason": "The story materially concerns trust, permissions, privacy, or governance.",
        }
    return None


def prepare_bridges(editorial: dict[str, Any], out: Path) -> dict[str, Any]:
    rules = []
    for idx, candidate in enumerate(editorial.get("candidates") or [], start=1):
        rule = bridge_rule(candidate, idx)
        if rule and rule["title_keywords"]:
            rules.append(rule)
    dump(out / "book-bridge-map.json", {
        "schema_version": "1.0.0",
        "series_title": "Generative AI Professional Series",
        "series_url": "https://generative-ai-professional-series.gtome.chatgpt.site/",
        "rules": rules,
    })
    return {"rule_count": len(rules), "rules": rules}


def mechanism_for(candidate: dict[str, Any]) -> tuple[str, str]:
    text = story_text(candidate).lower()
    if "skill" in text:
        return ("reusable-skill-control-plane", "Show a reusable Agent Skill package connecting instructions, tools, approval gates, evidence checks, and repeatable outputs.")
    if any(x in text for x in ("observability", "telemetry", "trace")):
        return ("agent-observability-trace", "Show an agent execution trace linking model calls, tool calls, latency, failures, retries, and review evidence.")
    if any(x in text for x in ("confidential", "privacy", "security")):
        return ("trusted-inference-boundary", "Show sensitive prompts and context entering an attested execution boundary, with protected model execution and controlled outputs.")
    if any(x in text for x in ("evaluation", "benchmark", "reproduc")):
        return ("evaluation-harness", "Show a reproducible evaluation harness separating tasks, model/harness configuration, recorded runs, metrics, and failure classes.")
    if any(x in text for x in ("retrieval", "grounding", "provenance")):
        return ("claim-evidence-provenance", "Show retrieved evidence flowing through provenance checks into claim-level grounded generation and reviewer verification.")
    if any(x in text for x in ("workflow", "automation", "agent")):
        return ("governed-agent-workflow", "Show a governed multi-step agent workflow with scoped tools, checkpoints, evidence capture, and human review.")
    return ("story-specific-system-map", "Build a story-specific explanatory system map showing the development's inputs, mechanism, controls, outputs, and practical consequence.")


def prepare_image_request(edition_date: str, editorial: dict[str, Any], output_root: Path) -> dict[str, Any]:
    requests = []
    candidates = editorial.get("candidates") or []
    if len(candidates) != 6:
        raise SystemExit("image request requires exactly six selected editorial candidates")
    for idx, candidate in enumerate(candidates, start=1):
        composition, mechanism = mechanism_for(candidate)
        requests.append({
            "ordinal": idx,
            "story_id": candidate["candidate_id"],
            "headline": candidate["title"],
            "source_url": candidate["url"],
            "summary": candidate.get("summary"),
            "why_it_matters": candidate.get("why_it_matters"),
            "requested_path": f"briefs/images/{edition_date}/{idx:02d}-{safe_id(candidate['title'])[:48]}.webp",
            "composition_id": f"{composition}-{idx}",
            "mechanism_brief": mechanism,
            "required_standard": {
                "width": 1200,
                "height": 630,
                "preferred_format": "webp",
                "white_or_near_white_background": True,
                "professional_textbook_editorial": True,
                "story_specific_mechanism": True,
                "high_information_density": True,
                "unique_composition": True,
                "no_photos_or_people": True,
                "no_decorative_collage": True,
                "no_sparse_generic_box_arrow": True,
                "no_clipped_or_overlapping_text": True,
                "generation_method": "openai_image_generation",
                "visual_review_required": True,
                "accepted_locked_required": True,
            },
        })
    package = {
        "schema_version": "1.0.0",
        "edition_date": edition_date,
        "story_count": 6,
        "generation_adapter_required": "OpenAI image generation",
        "paid_api_required": False,
        "workflow_boundary": "external_chatgpt_image_generation_then_resume_same_canonical_run",
        "requests": requests,
    }
    dump(output_root / "image-generation-request.json", package)
    return package


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare live media, Watchlist, book-bridge, and image-request inputs")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--state-root", required=True)
    ap.add_argument("--media-json", required=True)
    ap.add_argument("--legacy-root", default="legacy_snapshot")
    args = ap.parse_args()

    edition_date = args.edition_date
    date.fromisoformat(edition_date)
    root = Path(args.input_root)
    editorial = load(root / "editorial" / "source-catalog.json")
    canonical_edition = load(Path(args.state_root) / f"{edition_date}__production" / "edition.json")
    if canonical_edition.get("status") != "locked":
        raise SystemExit("canonical greenfield edition must be locked before downstream operational preparation")
    selected_ids = {
        str(x.get("story_id"))
        for x in (canonical_edition.get("data") or {}).get("stories", [])
    }
    selected_candidates = [
        x for x in editorial.get("candidates", [])
        if str(x.get("candidate_id")) in selected_ids
    ]
    if len(selected_ids) != 6 or len(selected_candidates) != 6:
        raise SystemExit("live operational preparation requires the exact six canonical locked stories")
    selected_editorial = {"schema_version": editorial.get("schema_version", "1.0.0"), "candidates": selected_candidates}
    media = load(Path(args.media_json))
    build = root / "build"

    media_result = prepare_media(media, build)
    watchlist_result = prepare_watchlist(edition_date, selected_editorial, Path(args.legacy_root), build)
    bridge_result = prepare_bridges(selected_editorial, build)
    image_request = prepare_image_request(edition_date, selected_editorial, root)

    manifest = {
        "schema_version": "1.0.0",
        "edition_date": edition_date,
        "canonical_entry_point": "start_daily_brief(date, mode)",
        "run_depth": "build_locked",
        "paid_api_calls": 0,
        "media": {
            "video_count": len(media_result["videos"]),
            "podcast_count": len(media_result["podcasts"]),
        },
        "watchlist": watchlist_result,
        "book_bridges": {"rule_count": bridge_result["rule_count"]},
        "image_request": {
            "story_count": image_request["story_count"],
            "generation_adapter_required": image_request["generation_adapter_required"],
            "boundary": image_request["workflow_boundary"],
        },
        "publication_attempted": False,
    }
    dump(root / "operational-input-manifest.json", manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
