#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CATEGORIES = (
    "agents_non_technical_people",
    "applied_genai_knowledge_workers",
    "technical_ai_engineering",
)
CUTOFF = "2026-09-23"


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_agent_skill(story: dict[str, Any]) -> bool:
    text = " ".join(
        [str(story.get("headline", "")), str(story.get("summary", ""))]
        + [str(x) for x in story.get("topics", [])]
    ).lower()
    return "agent skill" in text or ("reusable" in text and "skill" in text)


def resolve_edition(date: str, legacy: Path, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise SystemExit(f"explicit edition package missing: {path}")
        return path
    path = legacy / "_data" / "editions" / f"{date}.json"
    if not path.exists():
        raise SystemExit(
            "no authoritative edition input for requested date; "
            "provide --edition-json for the future explicit-date pathway"
        )
    return path


def prepare_editorial(edition: dict[str, Any], date: str, out: Path) -> list[dict[str, Any]]:
    stories = list(edition.get("stories", []))
    counts = {c: sum(s.get("focus") == c for s in stories) for c in CATEGORIES}
    if counts != {c: 2 for c in CATEGORIES}:
        raise SystemExit(f"edition does not satisfy exact 2/2/2 allocation: {counts}")

    ordered: list[dict[str, Any]] = []
    for category in CATEGORIES:
        ordered.extend(sorted((s for s in stories if s.get("focus") == category), key=lambda x: int(x.get("ordinal", 99))))
    skill_count = sum(is_agent_skill(s) for s in ordered)
    if skill_count != 1:
        raise SystemExit(f"edition must contain exactly one Agent Skills story for canonical run: {skill_count}")

    candidates = []
    sources = []
    for category in CATEGORIES:
        members = [s for s in ordered if s.get("focus") == category]
        source_id = f"legacy-{category}"
        ids = [s["story_id"] for s in members]
        sources.append({
            "source_id": source_id,
            "category_id": category,
            "fallback_tier": 0,
            "priority": 10,
            "cadence_days": 1,
            "last_checked": None,
            "enabled": True,
            "synthetic_metadata_failures": 0,
            "candidate_ids": ids,
        })
        for rank, story in enumerate(members):
            source = story.get("source", {})
            tags = list(story.get("topics", []))
            if is_agent_skill(story):
                tags.append("agent-skill")
            candidates.append({
                "candidate_id": story["story_id"],
                "source_id": source_id,
                "category_id": category,
                "title": story["headline"],
                "url": source.get("url") or source.get("normalized_url"),
                "published_at": source.get("publication_date") or story.get("event_date") or date,
                "summary": story.get("summary", ""),
                "why_it_matters": story.get("why_it_matters", ""),
                "quality_score": 100 - rank,
                "development_key": story["story_id"],
                "tags": tags,
                "deep_evidence": {
                    "claims": [{
                        "claim": story.get("summary", ""),
                        "source_url": source.get("url") or source.get("normalized_url"),
                    }]
                },
            })

    dump(out / "editorial" / "source-registry.json", {
        "schema_version": "1.0.0",
        "policy": {
            "freshness_days": 30,
            "max_metadata_attempts": 1,
            "max_fallback_tier": 0,
            "deep_retrieval_limit": 6,
        },
        "sources": sources,
    })
    dump(out / "editorial" / "source-catalog.json", {
        "schema_version": "1.0.0",
        "candidates": candidates,
    })
    dump(out / "editorial" / "novelty-index.json", {
        "schema_version": "1.0.0",
        "window_days": 30,
        "prior_items": [],
    })
    return ordered


def prepare_media(edition: dict[str, Any], date: str, out: Path) -> None:
    videos = []
    for key, item in (edition.get("worth_watching") or {}).items():
        if item.get("status") != "included":
            continue
        videos.append({
            "media_id": f"dab-video-{date}-{key}",
            "kind": "video",
            "title": item["title"],
            "url": item["url"],
            "published_at": item.get("upload_date") or date,
            "duration_minutes": round((item.get("runtime_seconds") or 0) / 60, 2),
            "available": True,
            "synthetic_verification_failures": 0,
        })
    podcasts = []
    for item in edition.get("podcasts", []):
        if item.get("status") != "included":
            continue
        podcasts.append({
            "media_id": item.get("item_id") or f"dab-podcast-{date}-{len(podcasts)+1}",
            "kind": "podcast",
            "title": item["title"],
            "url": item["url"],
            "published_at": item.get("publication_date") or date,
            "duration_minutes": round((item.get("runtime_seconds") or 0) / 60, 2),
            "available": True,
            "synthetic_verification_failures": 0,
        })
    if len(videos) != 2 or len(podcasts) != 2:
        raise SystemExit(f"media input must contain exactly two videos and two podcasts; got {len(videos)}/{len(podcasts)}")

    dump(out / "build" / "media-registry.json", {
        "schema_version": "1.0.0",
        "policy": {
            "max_verification_attempts": 1,
            "max_candidate_checks_per_kind": 4,
            "max_fallback_tier": 0,
        },
        "sources": [
            {
                "source_id": "legacy-video",
                "kind": "video",
                "fallback_tier": 0,
                "priority": 10,
                "enabled": True,
                "candidate_ids": [x["media_id"] for x in videos],
            },
            {
                "source_id": "legacy-podcast",
                "kind": "podcast",
                "fallback_tier": 0,
                "priority": 10,
                "enabled": True,
                "candidate_ids": [x["media_id"] for x in podcasts],
            },
        ],
    })
    dump(out / "build" / "media-catalog.json", {
        "schema_version": "1.0.0",
        "items": videos + podcasts,
    })


def prepare_watchlist(date: str, legacy: Path, out: Path, explicit: str | None) -> None:
    watch_path = Path(explicit) if explicit else legacy / "data" / "watchlist.json"
    if not watch_path.exists():
        raise SystemExit(f"watchlist input missing: {watch_path}")
    watch = load(watch_path)
    topics = []
    ids = []
    for row in watch.get("topics", []):
        topic_id = row["topic_id"]
        first = str(row.get("first_detected") or date)[:10]
        changed = str(row.get("updated_at") or first)[:10]
        topics.append({
            "topic_id": topic_id,
            "title": row.get("name") or topic_id,
            "summary": row.get("summary") or row.get("why_now") or "",
            "first_seen": first,
            "last_changed": changed,
            "active": True,
        })
        ids.append(topic_id)
    dump(out / "build" / "watchlist-registry.json", {
        "schema_version": "1.0.0",
        "sources": [{"source_id": "legacy-watchlist", "priority": 10, "topic_ids": ids}],
    })
    dump(out / "build" / "watchlist-catalog.json", {
        "schema_version": "1.0.0",
        "topics": topics,
    })


def prepare_bridges(out: Path) -> None:
    dump(out / "build" / "book-bridge-map.json", {
        "schema_version": "1.0.0",
        "series_title": "Generative AI Professional Series",
        "series_url": "https://leanpub.com/u/george-tome",
        "rules": [
            {
                "rule_id": "legacy-sep23-jetbrains-context",
                "priority": 10,
                "title_keywords": ["copilot", "jetbrains"],
                "book_id": "reliable-generative-ai-context-engineering",
                "section": "Designing High-Quality Contexts",
                "reason": "Shared skills, organizational instructions, tool approvals, and plan review map to the series treatment of governed context design.",
            }
        ],
    })


def prepare_images(stories: list[dict[str, Any]], out: Path) -> None:
    images = []
    for story in stories:
        image = story.get("image") or {}
        path = str(image.get("path") or "")
        fmt = Path(path).suffix.lower().lstrip(".")
        if fmt not in {"webp", "png"}:
            raise SystemExit(f"canonical production image for {story['story_id']} is not webp/png: {path}")
        images.append({
            "story_id": story["story_id"],
            "image_id": f"legacy-image-{story['story_id']}",
            "binary_seed": image.get("cache_key") or path or story["story_id"],
            "format": fmt,
            "width": int(image.get("width") or 1200),
            "height": int(image.get("height") or 630),
            "composition_id": story["story_id"],
            "mechanism_summary": story.get("why_it_matters") or story.get("summary") or story["headline"],
            "professional_textbook_editorial": True,
            "story_specific": True,
            "mechanism_explanatory": True,
            "high_detail": True,
            "high_information_density": True,
            "white_background": True,
            "sparse_generic_box_arrow": False,
            "reused_composition": False,
            "photo": False,
            "people": False,
            "decorative_collage": False,
            "clipped_text": False,
            "overlapping_text": False,
            "accept_on_attempt": 1,
            "source_path": path,
            "source_public_url": image.get("public_url"),
            "source_alt": image.get("alt"),
        })
    if len(images) != 6:
        raise SystemExit("exactly six story images are required")
    dump(out / "pre_release" / "image-catalog.json", {
        "schema_version": "1.0.0",
        "catalog_version": "legacy-import-1.0.0",
        "policy": {
            "max_attempts_per_image": 1,
            "width": 1200,
            "height": 630,
            "allowed_formats": ["webp", "png"],
        },
        "images": images,
    })


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--legacy-root", default="legacy_snapshot")
    ap.add_argument("--output-root", required=True)
    ap.add_argument("--edition-json")
    ap.add_argument("--watchlist-json")
    args = ap.parse_args()

    date = args.edition_date
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
        raise SystemExit("edition date must be YYYY-MM-DD")
    legacy = Path(args.legacy_root)
    edition_path = resolve_edition(date, legacy, args.edition_json)
    edition = load(edition_path)
    if edition.get("brief_date") != date:
        raise SystemExit("edition package date does not match requested date")

    out = Path(args.output_root)
    stories = prepare_editorial(edition, date, out)
    prepare_media(edition, date, out)
    prepare_watchlist(date, legacy, out, args.watchlist_json)
    prepare_bridges(out)
    prepare_images(stories, out)
    dump(out / "input-manifest.json", {
        "schema_version": "1.0.0",
        "edition_date": date,
        "edition_input": str(edition_path),
        "legacy_cutoff": CUTOFF,
        "canonical_entry_point": "start_daily_brief(date, mode)",
        "mode": "production",
        "prepared_story_ids": [s["story_id"] for s in stories],
        "reader_publication_authority": False,
    })
    print(json.dumps({"edition_date": date, "output_root": str(out), "story_count": 6, "media_count": 4}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
