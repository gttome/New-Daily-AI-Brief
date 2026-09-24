#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO = "gttome/New-Daily-AI-Brief"
READER_URL = "https://ndaib.gtome.chatgpt.site"
BLOCKER = "Not permitted until the old Daily AI Brief system is formally decommissioned."
FORBIDDEN_KEYS = {"site_project_id", "site_version_id", "deployment_id"}


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return default


def latest_receipt(root: Path) -> tuple[Path | None, dict[str, Any]]:
    rows = []
    for path in root.glob("docs/*PUBLICATION_RECEIPT*.json"):
        data = read_json(path, {})
        if data.get("edition_date"):
            rows.append((str(data["edition_date"]), path, data))
    if not rows:
        return None, {}
    _, path, data = sorted(rows, key=lambda x: x[0])[-1]
    return path, data


def normalize_story(story: dict[str, Any]) -> dict[str, Any]:
    src = story.get("source") or {}
    read = src.get("reading_evidence") or {}
    img = story.get("image") or {}
    topics = [str(x) for x in story.get("topics") or []]
    words = read.get("word_count")
    wpm = read.get("words_per_minute") or 200
    return {
        "ordinal": story.get("ordinal"),
        "focus": story.get("focus"),
        "headline": story.get("headline"),
        "agent_skills": any("agent skills" in x.lower() for x in topics),
        "freshness": (story.get("freshness") or {}).get("tier"),
        "novelty": (story.get("novelty") or {}).get("disposition"),
        "authoritative_source": src.get("availability_status") == "published",
        "source_organization": src.get("organization"),
        "source_publication_date": src.get("publication_date"),
        "reading_minutes": round(words / wpm) if words else None,
        "book_bridge": bool(story.get("book_bridge") or story.get("book")),
        "image_path": img.get("path"),
        "image_width": img.get("width"),
        "image_height": img.get("height"),
    }


def status_counts(items: list[dict[str, Any]], *keys: str) -> dict[str, int]:
    result: dict[str, int] = {}
    for item in items:
        value = "unknown"
        for key in keys:
            if item.get(key):
                value = str(item[key])
                break
        result[value] = result.get(value, 0) + 1
    return result


def sanitize_guard(value: Any) -> None:
    if isinstance(value, dict):
        leaked = FORBIDDEN_KEYS.intersection(value)
        if leaked:
            raise ValueError(f"private identifiers leaked into Command Center state: {sorted(leaked)}")
        for child in value.values():
            sanitize_guard(child)
    elif isinstance(value, list):
        for child in value:
            sanitize_guard(child)


def build(root: Path, main_sha: str) -> dict[str, Any]:
    template = read_json(root / "site/command-center/state.json", {})
    receipt_path, receipt = latest_receipt(root)
    if not receipt:
        raise SystemExit("no publication receipt found")
    date = str(receipt["edition_date"])
    edition = read_json(root / "legacy_snapshot/_data/editions" / f"{date}.json", {})
    watchlist = read_json(root / "legacy_snapshot/_data/watchlist.json", {})
    source_registry = read_json(root / "legacy_snapshot/_data/source-registry.json", {})
    wl_state = read_json(root / "legacy_snapshot/_data/watchlist-source-state.json", {})
    book = read_json(root / "legacy_snapshot/_data/book-reading.json", {})
    media_registry = read_json(root / "config/live-media-sources.json", {})

    stories = [normalize_story(x) for x in edition.get("stories") or []]
    allocation = {
        "technical_ai_engineering": sum(x["focus"] == "technical_ai_engineering" for x in stories),
        "applied_genai_knowledge_workers": sum(x["focus"] == "applied_genai_knowledge_workers" for x in stories),
        "agents_non_technical_people": sum(x["focus"] == "agents_non_technical_people" for x in stories),
    }
    skills = sum(bool(x["agent_skills"]) for x in stories)
    allocation_pass = allocation == {
        "technical_ai_engineering": 2,
        "applied_genai_knowledge_workers": 2,
        "agents_non_technical_people": 2,
    } and skills == 1

    images = [{
        "ordinal": x["ordinal"], "story": x["headline"], "path": x["image_path"],
        "dimensions": [x["image_width"], x["image_height"]],
        "format": "WebP" if str(x["image_path"] or "").lower().endswith(".webp") else "unknown",
        "generation_method": "per-slot generation method not separately encoded in durable receipt",
        "visual_qa": "accepted" if [x["image_width"], x["image_height"]] == [1200, 630] else "check",
        "locked": True, "regeneration_count": None, "quality_failure_reason": None,
    } for x in stories]

    topics = list(watchlist.get("topics") or watchlist.get("items") or [])
    changed = [(x.get("name") or x.get("title")) for x in topics if str(x.get("updated_at") or "").startswith(date)]
    registry = list(source_registry.get("sources") or [])
    wl_raw = wl_state.get("sources") or {}
    wl_sources = ([{"source_id": k, **(v if isinstance(v, dict) else {})} for k, v in wl_raw.items()]
                  if isinstance(wl_raw, dict) else list(wl_raw))
    podcasts = [{
        "title": x.get("title") or x.get("headline"),
        "source": (x.get("source") or {}).get("organization") or x.get("organization"),
        "publication_date": (x.get("source") or {}).get("publication_date") or x.get("publication_date"),
        "runtime": x.get("runtime") or x.get("duration"),
        "verification": "confirmed in canonical edition",
    } for x in edition.get("podcasts") or []]

    p = template
    p["snapshot_generated_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    p["source"].update({
        "main_sha": main_sha,
        "publication_receipt": receipt_path.as_posix() if receipt_path else None,
        "reader_source_sha": receipt.get("repository_source_sha"),
    })
    warnings = list(receipt.get("remaining_verification") or [])
    p["executive"].update({
        "edition_date": date,
        "overall_state": "Verified" if receipt.get("deployment_status") == "succeeded" else "Needs attention",
        "current_checkpoint": receipt_path.as_posix() if receipt_path else "Unavailable",
        "latest_successful_edition": date,
        "latest_publication_timestamp": edition.get("published_at"),
        "site_version": receipt.get("site_version"),
        "critical_defects": receipt.get("known_critical_defects", 0),
        "high_defects": receipt.get("known_high_defects", 0),
        "warning_count": len(warnings),
        "reader_health": "Verified with live-feed retrieval limitation" if warnings else "Verified",
        "old_system_decommissioned": False,
        "schedule_readiness": "Blocked pending old-system decommissioning",
    })
    p["stories"] = {"count": len(stories), "allocation": allocation, "agent_skills_count": skills,
                    "allocation_pass": allocation_pass, "items": stories}
    p["images"] = {"accepted_count": receipt.get("accepted_image_count", len(images)), "items": images}
    p["media"].update({
        "video_count": receipt.get("videos", 0), "podcast_count": receipt.get("podcasts", len(podcasts)),
        "videos": [{"slot": i + 1, "details": "Latest selected-video metadata is not separately encoded in the current durable publication receipt."}
                   for i in range(int(receipt.get("videos", 0) or 0))],
        "podcasts": podcasts,
        "video_source_registry_count": len(media_registry.get("video_sources") or []),
        "podcast_source_registry_count": len(media_registry.get("podcast_sources") or []),
    })
    p["watchlist"].update({
        "active_topics": len(topics),
        "new_today": (receipt.get("watchlist") or {}).get("new"),
        "updated_today": (receipt.get("watchlist") or {}).get("updated"),
        "carried_forward": (receipt.get("watchlist") or {}).get("carried_forward"),
        "changed_topics": changed,
        "source_state_updated_at": wl_state.get("updated_at"),
    })
    refs, editions = book.get("references") or {}, book.get("editions") or {}
    p["book_bridges"].update({
        "reference_count": len(refs), "edition_mapping_count": len(editions),
        "latest_edition_explicit_bridge_count": sum(bool(x["book_bridge"]) for x in stories),
    })
    feedback = receipt.get("live_feedback") or {}
    p["reader_site"].update({
        "html_page_count": (receipt.get("history") or {}).get("html_pages"),
        "archive_item_count": (receipt.get("history") or {}).get("archive_items"),
        "edition_count": (receipt.get("history") or {}).get("editions"),
        "ratings": feedback.get("event_writes") or "transport present",
        "sharing": feedback.get("copy_link") or "transport present",
        "comments": feedback.get("rating_comment_write_tests") or "transport present",
        "watchlist_interactions": feedback.get("watchlist_reads") or "transport present",
        "site_deployment_state": receipt.get("deployment_status"),
        "site_version": receipt.get("site_version"),
        "live_edition_url": receipt.get("brief_url") or f"{READER_URL}/briefs/{date}/",
    })
    for gate in p["readiness_gates"]:
        if gate["name"].startswith("Canonical 2/2/2"):
            gate.update(state="passed" if allocation_pass else "check", evidence=f"{date} canonical edition")
        elif gate["name"] == "Native Site publication proven":
            gate.update(state="passed" if receipt.get("deployment_status") == "succeeded" else "check",
                        evidence=f"Reader Site version {receipt.get('site_version')}")
        elif gate["name"] == "Zero Critical defects":
            gate.update(state="passed" if receipt.get("known_critical_defects", 0) == 0 else "blocked",
                        evidence=receipt.get("known_critical_defects", 0))
        elif gate["name"] == "Zero High defects":
            gate.update(state="passed" if receipt.get("known_high_defects", 0) == 0 else "blocked",
                        evidence=receipt.get("known_high_defects", 0))
    p["schedules"] = {
        "creation_permitted": False, "old_system_decommissioned": False, "blocker": BLOCKER,
        "planned": [
            {"name": "Publisher", "time": "07:00", "timezone": "America/Chicago", "created": False, "enabled": False, "status": "Not yet permitted"},
            {"name": "Validation/Repair", "time": "09:00", "timezone": "America/Chicago", "created": False, "enabled": False, "status": "Not yet permitted"},
        ],
    }
    p["run_history"] = [{
        "edition": date, "start": None, "end": edition.get("published_at"), "elapsed_seconds": None,
        "stages_reached": "Live Verification", "completion_state": "published_verified" if receipt.get("deployment_status") == "succeeded" else "unknown",
        "attempts": None, "resumes": None, "failures": 0 if receipt.get("known_critical_defects", 0) == 0 and receipt.get("known_high_defects", 0) == 0 else None,
        "repairs": None, "source_scans": None, "deep_retrievals": None, "image_generations": None,
        "media_checks": None, "qa_counts": None, "site_publication_result": receipt.get("deployment_status"),
        "note": "Exact run timings/counts are not invented when absent from durable evidence; live GitHub Actions metadata is loaded separately by the private UI when available.",
    }]
    p["source_health"].update({
        "source_registry_total": len(registry), "source_registry_status": status_counts(registry, "status"),
        "watchlist_source_total": len(wl_sources), "watchlist_source_status": status_counts(wl_sources, "status", "state"),
        "watchlist_source_state_updated_at": wl_state.get("updated_at"),
        "video_source_registry_total": len(media_registry.get("video_sources") or []),
        "podcast_source_registry_total": len(media_registry.get("podcast_sources") or []),
    })
    p["incidents"].update({"latest_recovery_checkpoint": receipt_path.as_posix() if receipt_path else None})
    p["warnings"] = warnings
    p["command_center_site"].update({"identifier": "npccs", "publication_state": "source_ready_private_publish_required",
                                     "live_url": None, "public_pages_deployment_allowed": False})
    sanitize_guard(p)
    if p["schedules"]["creation_permitted"] or any(x["created"] or x["enabled"] for x in p["schedules"]["planned"]):
        raise ValueError("schedule hard-cutover invariant violated")
    return p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--main-sha", required=True)
    ap.add_argument("--output", default="site/command-center/state.json")
    args = ap.parse_args()
    root = Path(args.repo_root).resolve()
    out = Path(args.output)
    if not out.is_absolute():
        out = root / out
    state = build(root, args.main_sha)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(out), "edition_date": state["executive"]["edition_date"],
                      "stories": state["stories"]["count"], "schedules_created": False, "schedules_enabled": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
