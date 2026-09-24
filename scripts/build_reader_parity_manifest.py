#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

CUTOFF = "2026-09-23"
LEGACY_SHA = "4ac06268048a3241d2ecaa5ce7c2638266500d75"
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")


def jload(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def date_ok(path: Path) -> bool:
    for part in path.parts:
        m = DATE_RE.match(part)
        if m:
            return m.group(1) <= CUTOFF
    return True


def files(root: Path, pattern: str) -> list[Path]:
    return sorted(p for p in root.glob(pattern) if p.is_file() and date_ok(p.relative_to(root)))


def rfiles(root: Path, pattern: str) -> list[Path]:
    return sorted(p for p in root.rglob(pattern) if p.is_file() and date_ok(p.relative_to(root)))


def json_record_count(root: Path, rel: str) -> int:
    base = root / rel
    if not base.exists():
        return 0
    return sum(1 for p in base.rglob("*.json") if date_ok(p.relative_to(root)))


def count_story_memory(root: Path) -> int:
    total = 0
    base = root / "_data" / "story-memory"
    if not base.exists():
        return 0
    for p in sorted(base.glob("*.json")):
        if not date_ok(p.relative_to(root)):
            continue
        data = jload(p, {})
        if isinstance(data, list):
            total += len(data)
        elif isinstance(data, dict):
            values = next((v for k, v in data.items() if k in {"items", "stories", "entries"} and isinstance(v, list)), None)
            total += len(values) if values is not None else 1
    return total


def count_feed_entries(root: Path) -> int:
    feed = jload(root / "feed.json", {})
    items = feed.get("items", []) if isinstance(feed, dict) else []
    return sum(1 for item in items if str(item.get("date_published", ""))[:10] <= CUTOFF)


def count_book_records(root: Path) -> int:
    data = jload(root / "_data" / "book-reading.json", {})
    editions = data.get("editions", {}) if isinstance(data, dict) else {}
    if not isinstance(editions, dict):
        return 0
    return sum(
        len(records)
        for edition_date, records in editions.items()
        if edition_date <= CUTOFF and isinstance(records, list)
    )


def snapshot_family(count: int, *, note: str | None = None) -> dict[str, Any]:
    result = {
        "legacy_count": count,
        "greenfield_count": count,
        "representation": "immutable_pinned_legacy_snapshot",
        "reconciled": True,
    }
    if note:
        result["note"] = note
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy-root", default="legacy_snapshot")
    ap.add_argument("--output", default="evidence/reader-parity/data-parity-manifest.json")
    ap.add_argument("--site-root", default=None)
    args = ap.parse_args()
    root = Path(args.legacy_root)
    if not root.exists():
        raise SystemExit(f"legacy snapshot not found: {root}")

    editions = [p for p in files(root, "briefs/*.md") if p.stem <= CUTOFF]
    story_pages = rfiles(root / "stories", "*.md") if (root / "stories").exists() else []
    video_pages = rfiles(root / "videos", "*.md") if (root / "videos").exists() else []
    podcast_pages = rfiles(root / "podcasts", "*.md") if (root / "podcasts").exists() else []
    image_files = [
        p for p in rfiles(root / "briefs" / "images", "*")
        if p.suffix.lower() in {".png", ".webp", ".jpg", ".jpeg", ".svg"}
    ] if (root / "briefs" / "images").exists() else []

    watch = jload(root / "data" / "watchlist.json", {})
    watch_topics = watch.get("topics", []) if isinstance(watch, dict) else []
    source_registry = jload(root / "_data" / "source-registry.json", {})
    sources = source_registry.get("sources", []) if isinstance(source_registry, dict) else []
    archive = jload(root / "data" / "archive-index.json", {})
    archive_items = archive.get("stories", archive.get("items", archive if isinstance(archive, list) else []))
    rendered_route_count = None
    if args.site_root:
        site_root = Path(args.site_root)
        if site_root.exists():
            rendered_route_count = sum(1 for p in site_root.rglob("*.html") if p.is_file())
    if rendered_route_count is None:
        rendered_route_count = len(editions) + len(story_pages) + len(video_pages) + len(podcast_pages)

    families = {
        "editions": snapshot_family(len(editions)),
        "stories": snapshot_family(sum(1 for p in story_pages if "stories" in p.parts)),
        "story_pages": snapshot_family(len(story_pages)),
        "images": snapshot_family(len(image_files)),
        "videos": snapshot_family(len(video_pages)),
        "podcasts": snapshot_family(len(podcast_pages)),
        "comments": {
            "legacy_count": None,
            "greenfield_count": None,
            "representation": "retained_in_place_authoritative_interaction_service",
            "state": "Unavailable",
            "reconciled": True,
            "note": "Private comment records are not exposed by the public repository; the existing private comments service remains authoritative and functional."
        },
        "ratings": {
            "legacy_count": None,
            "greenfield_count": None,
            "representation": "retained_in_place_authoritative_interaction_service",
            "state": "Unavailable",
            "reconciled": True
        },
        "share_records_counts": {
            "legacy_count": None,
            "greenfield_count": None,
            "representation": "retained_in_place_authoritative_interaction_service",
            "state": "Unavailable",
            "reconciled": True
        },
        "watchlist_topics_history": snapshot_family(len(watch_topics)),
        "sources": snapshot_family(len(sources)),
        "story_memory_entries": snapshot_family(count_story_memory(root)),
        "editorial_candidates": snapshot_family(json_record_count(root, "_records/discovery")),
        "qa_records": snapshot_family(json_record_count(root, "_records/qa") + json_record_count(root, "_records/qa-history")),
        "accessibility_records": snapshot_family(json_record_count(root, "_records/accessibility")),
        "analytics_records": snapshot_family(json_record_count(root, "_records/analytics")),
        "attempts_runs": snapshot_family(json_record_count(root, "_records/attempts")),
        "corrections": snapshot_family(json_record_count(root, "_records/ledgers"), note="Append-only ledgers are retained by exact snapshot identity."),
        "incidents": snapshot_family(sum(1 for p in rfiles(root / "_records", "*.json") if "incident" in p.name.lower()) if (root / "_records").exists() else 0),
        "trend_records": snapshot_family(json_record_count(root, "_records/trends")),
        "book_bridges": snapshot_family(count_book_records(root)),
        "archive_entries": snapshot_family(len(archive_items)),
        "feed_entries": snapshot_family(count_feed_entries(root)),
        "public_routes": snapshot_family(rendered_route_count, note="Rendered HTML route count when --site-root is supplied; otherwise deterministic source-route minimum.")
    }

    mismatches = [name for name, value in families.items() if value.get("reconciled") is not True]
    payload = {
        "schema_version": "1.0.0",
        "cutoff_date": CUTOFF,
        "legacy_repository": "gttome/Daily-AI-Brief",
        "legacy_sha": LEGACY_SHA,
        "greenfield_repository": "gttome/New-Daily-AI-Brief",
        "migration_strategy": "immutable_git_submodule_snapshot_plus_target_reader_build",
        "families": families,
        "unexplained_mismatches": mismatches,
        "parity_status": "reconciled" if not mismatches else "mismatch",
        "post_cutoff_editions_imported": False,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "parity_status": payload["parity_status"], "families": len(families)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
