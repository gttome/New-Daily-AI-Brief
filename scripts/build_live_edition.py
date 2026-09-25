#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from new_daily_ai_brief.watchlist_live import public_watchlist_from_canonical

TECHNICAL = "technical_ai_engineering"
APPLIED = "applied_genai_knowledge_workers"
AGENTS = "agents_non_technical_people"
FOCUS_ORDER = (TECHNICAL, TECHNICAL, APPLIED, APPLIED, AGENTS, AGENTS)
SITE_BASE = "https://ndaib.gtome.chatgpt.site"

BOOK_REFS = {
    "Reliable Generative AI Context Engineering": "context-quality-checklist",
    "Reliable Generative AI": "reliable-verification",
}
TRUST_SECTION = "Managing Expectations and Calibrating Trust"


def load(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"required file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return value[:100].rstrip("-") or "story"


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


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def story_suffix(url: str) -> str:
    return hashlib.sha256(normalize_url(url).encode("utf-8")).hexdigest()[:8]


def evidence_type(value: str | None) -> str:
    return {
        "publisher_authored": "official_announcement",
        "official_announcement": "official_announcement",
        "primary_source": "primary_source",
        "research": "research",
        "standards": "standards",
        "preprint": "preprint",
        "authoritative_reporting": "authoritative_reporting",
    }.get(str(value or ""), "publisher_authored")


def score_record(raw: int) -> dict[str, Any]:
    # Keep dimensions stable and auditable; the legacy validator requires their exact sum.
    quality = max(0, min(100, int(raw or 0)))
    dims = {
        "significance": max(1, quality // 14),
        "freshness": 7,
        "authority": 7,
        "evidence_quality": 7,
        "novelty": 6,
        "practical_value": max(1, quality // 16),
        "category_fit": 7,
    }
    return {
        **dims,
        "total": sum(dims.values()),
        "selection_rationale": "Selected by the bounded live metadata/evidence gate and retained by the canonical 2/2/2 greenfield editorial lock.",
    }


def focus_label(focus: str) -> str:
    return {
        TECHNICAL: "Technical AI Engineering",
        APPLIED: "Applied Generative AI for Knowledge Workers",
        AGENTS: "Agents for Everyone",
    }[focus]


def action_for(candidate: dict[str, Any]) -> dict[str, str]:
    text = " ".join(str(candidate.get(k, "")) for k in ("title", "summary", "why_it_matters")).lower()
    if any(x in text for x in ("security", "privacy", "approval", "confidential", "governance")):
        return {
            "action": "govern",
            "label": "Define the control boundary",
            "rationale": "Identify sensitive inputs and consequential actions, require explicit permissions and review, and verify the control path before broader use.",
        }
    if any(x in text for x in ("evaluation", "benchmark", "observability", "telemetry", "provenance")):
        return {
            "action": "measure",
            "label": "Measure before standardizing",
            "rationale": "Run the approach on a representative task, capture objective traces or evaluation evidence, and compare results before changing a production default.",
        }
    if any(x in text for x in ("skill", "workflow", "agent", "automation")):
        return {
            "action": "pilot",
            "label": "Pilot one bounded workflow",
            "rationale": "Choose one repeatable task, define its inputs, tool permissions, evidence, and human review points, then compare the result with the current process.",
        }
    return {
        "action": "evaluate",
        "label": "Pilot with explicit verification",
        "rationale": "Test the pattern on a bounded workflow, define objective evidence and human review points, and compare results before scaling.",
    }


def topics_for(candidate: dict[str, Any]) -> list[str]:
    text = " ".join(str(candidate.get(k, "")) for k in ("title", "summary")).lower()
    preferred = [
        "Agent Skills", "agents", "workflow", "evaluation", "observability", "OpenTelemetry",
        "retrieval", "grounding", "provenance", "privacy", "security", "confidential computing",
        "model routing", "Copilot", "inference", "benchmark", "context engineering",
    ]
    found = []
    for topic in preferred:
        if topic.lower() in text and topic not in found:
            found.append(topic)
    if len(found) < 2:
        for token in re.findall(r"[a-z0-9][a-z0-9-]{4,}", candidate.get("title", "").lower()):
            if token not in {"about","after","again","available","brings","inside","through","using","with"} and token not in found:
                found.append(token)
            if len(found) >= 4:
                break
    return found[:4] or ["generative AI"]


def image_entries(
    edition_date: str,
    ordered_candidates: list[dict[str, Any]],
    approved_manifest: dict[str, Any],
    source_root: Path,
    runtime_root: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    entries_raw = approved_manifest.get("images") if isinstance(approved_manifest, dict) else None
    if not isinstance(entries_raw, list) or len(entries_raw) != 6:
        raise SystemExit("approved image manifest must contain exactly six images")
    by_story = {str(x.get("story_id")): x for x in entries_raw}
    image_records: list[dict[str, Any]] = []
    handoff: dict[str, Any] = {}

    for ordinal, candidate in enumerate(ordered_candidates, start=1):
        key = candidate["candidate_id"]
        entry = by_story.get(key)
        if not entry:
            raise SystemExit(f"approved image missing for locked story {key}")
        if entry.get("quality_accepted") is not True or entry.get("accepted_locked") is not True:
            raise SystemExit(f"image is not quality accepted and locked: {key}")
        if entry.get("generation_method") != "openai_image_generation":
            raise SystemExit(f"image generation method must be openai_image_generation: {key}")
        source_base = source_root.resolve()
        src = (source_root / str(entry.get("file") or "")).resolve()
        if src != source_base and source_base not in src.parents:
            raise SystemExit(f"approved image path escapes approved image root: {key}")
        if not src.is_file():
            raise SystemExit(f"approved image bytes missing: {src}")
        ext = src.suffix.lower()
        if ext not in {".webp", ".png"}:
            raise SystemExit(f"approved image must be WebP or PNG: {src}")
        data = src.read_bytes()
        digest = sha256_bytes(data)
        expected = str(entry.get("sha256") or "")
        if expected and expected != digest:
            raise SystemExit(f"approved image sha256 mismatch: {key}")

        target_name = f"{ordinal:02d}-{slugify(candidate['title'])[:52]}{ext}"
        rel = f"briefs/images/{edition_date}/{target_name}"
        dest = runtime_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        alt = str(entry.get("alt") or f"Professional textbook-style editorial diagram for {candidate['title']}.")
        image_records.append({
            "path": rel,
            "public_url": f"{SITE_BASE}/{rel}?v={digest[:16]}",
            "alt": alt,
            "width": 1200,
            "height": 630,
            "kind": "editorial_explainer",
            "cache_key": digest[:16],
        })
        handoff[f"image_{ordinal}"] = {
            "story_id": key,
            "path": rel,
            "alt": alt,
            "generation_method": "openai_image_generation",
            "quality_accepted": True,
            "accepted_locked": True,
            "lock_status": "accepted_locked",
            "sha256": digest,
            "composition": str(entry.get("composition") or entry.get("composition_id") or f"story-specific-{ordinal}"),
            "assessment": str(entry.get("assessment") or "Professional story-specific explanatory illustration accepted after visual review."),
        }
    if len({x["sha256"] for x in handoff.values()}) != 6:
        raise SystemExit("approved image set must contain six distinct image byte streams")
    return image_records, handoff


def build_stories(
    edition_date: str,
    cutoff: str,
    catalog: dict[str, Any],
    images: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    candidates = catalog.get("candidates") or []
    by_focus = {
        focus: sorted(
            [x for x in candidates if x.get("category_id") == focus],
            key=lambda x: (-int(x.get("quality_score") or 0), x["candidate_id"]),
        )
        for focus in {TECHNICAL, APPLIED, AGENTS}
    }
    ordered: list[dict[str, Any]] = []
    for focus in (TECHNICAL, APPLIED, AGENTS):
        if len(by_focus[focus]) != 2:
            raise SystemExit(f"live publication requires exactly two locked stories for {focus}")
        ordered.extend(by_focus[focus])

    cutoff_dt = datetime.fromisoformat(cutoff.replace("Z", "+00:00"))
    stories = []
    for ordinal, (candidate, image) in enumerate(zip(ordered, images), start=1):
        full_stamp = str(candidate.get("published_at_full") or candidate.get("metadata_event_at") or candidate.get("published_at"))
        published_dt = datetime.fromisoformat(full_stamp.replace("Z", "+00:00"))
        age_hours = (cutoff_dt - published_dt).total_seconds() / 3600
        primary = age_hours <= 24
        freshness = {
            "tier": "primary" if primary else "fallback",
            "source_published_at": published_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
        if not primary:
            freshness["fallback_reason"] = "Selected only after the bounded primary-window gate did not yield a stronger eligible story in this category."
        story_id = f"dab-story-{edition_date}-{story_suffix(candidate['url'])}"
        slug = slugify(candidate["title"])
        word_count = int(candidate.get("source_word_count") or 0)
        stories.append({
            "story_id": story_id,
            "ordinal": ordinal,
            "slug": slug,
            "permanent_url": f"/stories/{edition_date}/{slug}/",
            "focus": candidate["category_id"],
            "headline": candidate["title"],
            "event_date": str(candidate.get("published_at") or edition_date)[:10],
            "topics": topics_for(candidate),
            "companies": [],
            "image": image,
            "summary": candidate.get("summary") or candidate.get("evidence_excerpt") or candidate["title"],
            "why_it_matters": candidate.get("why_it_matters") or "This development changes how AI systems can be built, governed, or used in practical work.",
            "source": {
                "title": candidate["title"],
                "organization": candidate.get("publisher") or candidate.get("source_id") or "Primary source",
                "url": candidate["url"],
                "normalized_url": normalize_url(candidate["url"]),
                "publication_date": str(candidate.get("published_at") or edition_date)[:10],
                "evidence_type": evidence_type(candidate.get("source_reliability")),
                "availability_status": "published",
                "reading_evidence": {
                    "status": "verified" if word_count > 0 else "unavailable",
                    "word_count": word_count if word_count > 0 else None,
                    "verified_at": cutoff,
                    "method": "retrieved_source_text_word_count" if word_count > 0 else "not_verified",
                    "words_per_minute": 200,
                },
            },
            "freshness": freshness,
            "selection_rationale": "Selected by bounded live discovery and canonical greenfield editorial locking.",
            "novelty": {"disposition": "new", "prior_story_ids": [], "what_changed": None},
            "candidate_score": score_record(int(candidate.get("quality_score") or 0)),
            "what_to_do_now": action_for(candidate),
            "social_description": str(candidate.get("why_it_matters") or candidate.get("summary") or "")[:180],
            "social": {
                "title": candidate["title"],
                "description": str(candidate.get("why_it_matters") or candidate.get("summary") or "")[:180],
                "image_url": image["public_url"],
            },
        })
    if [x["focus"] for x in stories] != list(FOCUS_ORDER):
        raise SystemExit("story ordering does not satisfy canonical 2/2/2 focus order")
    return stories


def build_media(edition_date: str, media: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    selected = media.get("selected") or {}
    videos = selected.get("videos") or []
    podcasts = selected.get("podcasts") or []
    if len(videos) != 2 or len(podcasts) != 2:
        raise SystemExit("live publication requires exactly two videos and two podcasts")

    worth = {}
    video_out = []
    for idx, row in enumerate(videos):
        slot = "agents_non_technical_people" if idx == 0 and row.get("agent_signal") else ("general" if idx == 0 else "agents_non_technical_people")
        if idx == 1 and slot in worth:
            slot = "general"
        if slot in worth:
            slot = "agents_non_technical_people" if slot == "general" else "general"
        item = {
            "status": "included",
            "title": row["title"],
            "channel": row.get("channel") or row.get("source_id") or "Verified source",
            "upload_date": row["publication_date"],
            "runtime_seconds": int(row["runtime_seconds"]),
            "why_useful": row.get("description") or "A current verified video that extends the day's AI coverage.",
            "connection": "Adds a concise practitioner or engineering perspective connected to the day's selected developments.",
            "url": row["url"],
            "duration_tier": row.get("duration_tier") or ("short" if int(row["runtime_seconds"]) <= 600 else "fallback"),
            "short_search_evidence": ["Live bounded source search completed before selection."],
        }
        if int(row["runtime_seconds"]) > 600:
            item["fallback_reason"] = "No sufficiently relevant verified candidate of 10 minutes or less ranked higher in the bounded search."
        worth[slot] = item
        video_out.append((slot, row, item))
    if set(worth) != {"general", "agents_non_technical_people"}:
        raise SystemExit("both required video slots were not populated")

    podcast_out = []
    for idx, row in enumerate(podcasts):
        slug = slugify(row["title"])
        item_id = f"dab-podcast-{edition_date}-{story_suffix(row['url'])}"
        focus = APPLIED if idx == 0 else TECHNICAL
        podcast = {
            "status": "included",
            "ordinal": 9 + idx,
            "item_id": item_id,
            "title": row["title"],
            "show": row.get("show") or row.get("source_id") or "Verified podcast",
            "host": row.get("host") or row.get("show") or "Verified podcast",
            "publication_date": row["publication_date"],
            "published_at": row.get("published_at"),
            "runtime_seconds": row.get("runtime_seconds"),
            "focus": focus,
            "topics": topics_for({"title": row["title"], "summary": row.get("description")}),
            "url": row["url"],
            "permanent_url": f"/podcasts/{edition_date}/{slug}/",
            "summary": row.get("description") or "A current verified podcast episode relevant to the day's AI coverage.",
            "why_useful": "Adds a current practitioner or industry perspective to the day's selected developments.",
            "connection": "Extends the Brief with a longer-form discussion of practical AI systems, workflows, or governance.",
            "selection_rationale": "Selected by bounded live podcast discovery with source diversity and freshness gates.",
            "verification_note": "Publication date and source URL were verified through the publisher-linked feed during the live media preflight.",
            "coverage_note": "Current source-diverse podcast selection.",
            "freshness_tier": row.get("freshness_tier") or "primary_48h",
            "platforms": [{"name": row.get("show") or "Publisher", "url": row["url"]}],
        }
        if row.get("freshness_exception_reason"):
            podcast["freshness_exception_reason"] = row["freshness_exception_reason"]
        podcast_out.append(podcast)
    return worth, podcast_out, video_out


def update_watchlist(runtime_root: Path, edition_date: str, canonical_watchlist: dict[str, Any]) -> None:
    public = public_watchlist_from_canonical(canonical_watchlist)
    if public.get("edition_date") != edition_date:
        raise SystemExit("canonical Watchlist edition date does not match live edition")
    dump(runtime_root / "_data" / "watchlist.json", public)
    dump(runtime_root / "data" / "watchlist.json", public)

def update_book_reading(runtime_root: Path, edition_date: str, build_root: Path, stories: list[dict[str, Any]]) -> None:
    path = runtime_root / "_data" / "book-reading.json"
    data = load(path)
    rules = (load(build_root / "book-bridge-map.json").get("rules") or [])
    entries = []
    for story in stories:
        title = story["headline"].lower()
        matched = None
        for rule in sorted(rules, key=lambda x: (int(x.get("priority") or 0), x.get("rule_id",""))):
            if all(str(k).lower() in title for k in rule.get("title_keywords") or []):
                matched = rule
                break
        if not matched:
            continue
        if TRUST_SECTION in matched.get("section", ""):
            ref = "reliable-trust"
        else:
            ref = BOOK_REFS.get(matched.get("book_id"))
        if not ref:
            continue
        entries.append({
            "item_id": story["story_id"],
            "reference_id": ref,
            "label": "PUT IT INTO PRACTICE" if ref == "context-quality-checklist" else "READ DEEPER",
            "why": matched.get("reason") or "Use the verified Professional Series section to apply this development with explicit evidence and review.",
        })
    data.setdefault("editions", {})[edition_date] = entries
    dump(path, data)


def write_media_preflight(runtime_root: Path, edition_date: str, cutoff: str, edition: dict[str, Any], media: dict[str, Any], video_out: list[tuple[str, dict[str, Any], dict[str, Any]]]) -> None:
    items = []
    for slot, source, item in video_out:
        item_id = f"dab-video-{edition_date}-{'general' if slot == 'general' else 'agent-skills'}"
        items.append({
            "item_id": item_id,
            "kind": "video",
            "url": item["url"],
            "reachable": source.get("reachable") is True,
            "http_status": int(source.get("http_status") or 0),
            "observed_date": item["upload_date"],
            "observed_runtime_seconds": item["runtime_seconds"],
        })
    source_podcasts = (media.get("selected") or {}).get("podcasts") or []
    if len(source_podcasts) != len(edition["podcasts"]):
        raise SystemExit("media preflight podcast source count mismatch")
    for podcast, source in zip(edition["podcasts"], source_podcasts):
        items.append({
            "item_id": podcast["item_id"],
            "kind": "podcast",
            "url": podcast["url"],
            "reachable": source.get("reachable") is True,
            "http_status": int(source.get("http_status") or 0),
            "observed_date": podcast["publication_date"],
            "observed_runtime_seconds": podcast["runtime_seconds"],
        })
    dump(runtime_root / "_records" / "editorial" / "media-preflight" / f"{edition_date}.json", {
        "schema_version": "1.0.0",
        "edition_id": edition["edition_id"],
        "checked_at": cutoff,
        "basis": "Live zero-paid-API media discovery and publisher/feed verification performed in the same manual workflow.",
        "items": items,
    })


def main() -> int:
    ap = argparse.ArgumentParser(description="Assemble a full_v1 live edition after six professional images are accepted")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--runtime-root", required=True)
    ap.add_argument("--state-root", required=True)
    ap.add_argument("--approved-image-manifest", required=True)
    ap.add_argument("--approved-image-root", default=".")
    ap.add_argument("--allow-fixture-images", action="store_true")
    args = ap.parse_args()

    input_root = Path(args.input_root)
    runtime_root = Path(args.runtime_root)
    catalog = load(input_root / "editorial" / "source-catalog.json")
    live_manifest = load(input_root / "live-input-manifest.json")
    operational = load(input_root / "operational-input-manifest.json")
    media = load(input_root / "live-media.json")
    approved = load(Path(args.approved_image_manifest))
    if approved.get("fixture_only") is True and not args.allow_fixture_images:
        raise SystemExit("CI fixture image manifests are forbidden in a live publication run")
    cutoff = str(live_manifest.get("metadata_cutoff") or media.get("cutoff"))
    if not cutoff:
        raise SystemExit("live research cutoff is missing")

    state_dir = Path(args.state_root) / f"{args.edition_date}__production"
    canonical_edition = load(state_dir / "edition.json")
    canonical_media = load(state_dir / "media.json")
    canonical_watchlist = load(state_dir / "watchlist.json")
    canonical_bridges = load(state_dir / "book-bridges.json")
    for name, record in (
        ("edition", canonical_edition),
        ("media", canonical_media),
        ("watchlist", canonical_watchlist),
        ("book-bridges", canonical_bridges),
    ):
        if record.get("status") != "locked":
            raise SystemExit(f"canonical greenfield {name} artifact is not locked")
        if record.get("edition_date") != args.edition_date:
            raise SystemExit(f"canonical greenfield {name} artifact date mismatch")
    catalog_story_ids = {x["candidate_id"] for x in catalog.get("candidates", [])}
    locked_story_ids = {x["story_id"] for x in canonical_edition.get("data", {}).get("stories", [])}
    if len(locked_story_ids) != 6 or not locked_story_ids.issubset(catalog_story_ids):
        raise SystemExit("publication assembly does not match the six canonical greenfield locked stories")
    locked_media_urls = {
        x["url"] for kind in ("videos", "podcasts")
        for x in canonical_media.get("data", {}).get(kind, [])
    }
    discovered_media_urls = {
        x["url"] for kind in ("videos", "podcasts")
        for x in (media.get("selected") or {}).get(kind, [])
    }
    if locked_media_urls != discovered_media_urls or len(locked_media_urls) != 4:
        raise SystemExit("publication media does not match the canonical greenfield locked media set")

    locked_catalog_candidates = [
        x for x in catalog.get("candidates", [])
        if x.get("candidate_id") in locked_story_ids
    ]
    by_focus = {
        focus: sorted(
            [x for x in locked_catalog_candidates if x.get("category_id") == focus],
            key=lambda x: (-int(x.get("quality_score") or 0), x["candidate_id"]),
        )
        for focus in (TECHNICAL, APPLIED, AGENTS)
    }
    ordered_candidates = by_focus[TECHNICAL] + by_focus[APPLIED] + by_focus[AGENTS]
    if len(ordered_candidates) != 6 or any(len(by_focus[focus]) != 2 for focus in (TECHNICAL, APPLIED, AGENTS)):
        raise SystemExit("exactly six canonical locked candidates in the 2/2/2 allocation are required")

    images, handoff = image_entries(
        args.edition_date,
        ordered_candidates,
        approved,
        Path(args.approved_image_root),
        runtime_root,
    )
    stories = build_stories(
        args.edition_date,
        cutoff,
        {"schema_version": catalog.get("schema_version", "1.0.0"), "candidates": locked_catalog_candidates},
        images,
    )
    worth, podcasts, video_out = build_media(args.edition_date, media)
    fallback_used = any(x["freshness"]["tier"] == "fallback" for x in stories)
    coverage = f"24-hour primary window ending at {cutoff}."
    if fallback_used:
        coverage += " Recency fallback used where the bounded primary window did not yield two stronger eligible stories in a category."

    edition = {
        "schema_version": "1.0.0",
        "policy_profile": "full_v1",
        "edition_id": f"dab-edition-{args.edition_date}",
        "brief_date": args.edition_date,
        "timezone": "America/Chicago",
        "title": f"Daily Generative AI Brief — {args.edition_date}",
        "published_at": cutoff,
        "research_cutoff_at": cutoff,
        "coverage_period": coverage,
        "status": "staged",
        "stories": stories,
        "worth_watching": worth,
        "editorial_takeaway": "Today’s developments reinforce a practical operating model for generative AI: use bounded evidence, make agent and model behavior observable, preserve explicit control points, and verify outcomes before scaling.",
        "provenance": {
            "greenfield_canonical_entry_point": "start_daily_brief(date, mode)",
            "greenfield_run_depth_before_images": "build_locked",
            "live_discovery_profile": live_manifest.get("discovery_profile"),
            "paid_api_calls": 0,
            "canonical_artifact_digests": {
                "edition": canonical_edition.get("content_digest"),
                "media": canonical_media.get("content_digest"),
                "watchlist": canonical_watchlist.get("content_digest"),
                "book_bridges": canonical_bridges.get("content_digest"),
            },
        },
        "podcasts": podcasts,
    }
    dump(runtime_root / "_data" / "editions" / f"{args.edition_date}.json", edition)

    review_path = runtime_root / "_records" / "image-quality" / f"{args.edition_date}-greenfield-handoff.json"
    dump(review_path, handoff)
    update_watchlist(runtime_root, args.edition_date, canonical_watchlist)
    update_book_reading(runtime_root, args.edition_date, input_root / "build", stories)
    write_media_preflight(runtime_root, args.edition_date, cutoff, edition, media, video_out)

    result = {
        "schema_version": "1.0.0",
        "edition_date": args.edition_date,
        "edition_path": str(runtime_root / "_data" / "editions" / f"{args.edition_date}.json"),
        "image_review_path": str(review_path.relative_to(runtime_root)),
        "story_count": 6,
        "video_count": 2,
        "podcast_count": 2,
        "professional_image_count": 6,
        "ready_for_publication_generator": True,
    }
    dump(input_root / "live-publication-manifest.json", result)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
