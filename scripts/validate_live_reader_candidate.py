#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from new_daily_ai_brief.watchlist_live import validate_public_watchlist

FORBIDDEN_READER_TEXT = (
    "GREENFIELD TEST",
    "PRE-CUTOVER",
    "Representative shadow data",
    "Owner acceptance environment",
    "GREENFIELD COMMAND CENTER",
)
HISTORICAL_REQUIRED = (
    "briefs/2026-08-17/index.html",
    "briefs/2026-09-23/index.html",
    "briefs-archive/index.html",
    "watchlist/index.html",
    "sources/index.html",
    "about/index.html",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate a live Daily AI Brief reader candidate without weakening historical parity")
    ap.add_argument("--site-root", required=True)
    ap.add_argument("--edition-json", required=True)
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--target-url", default="https://ndaib.gtome.chatgpt.site")
    ap.add_argument("--canonical-watchlist-json", required=True)
    args = ap.parse_args()

    root = Path(args.site_root)
    edition = json.loads(Path(args.edition_json).read_text(encoding="utf-8"))
    date = args.edition_date
    if edition.get("brief_date") != date:
        fail("edition date mismatch")
    if len(edition.get("stories") or []) != 6:
        fail("live edition must contain six stories")
    if len((edition.get("podcasts") or [])) != 2:
        fail("live edition must contain two podcasts")
    if sum(1 for x in (edition.get("worth_watching") or {}).values() if x.get("status") == "included") != 2:
        fail("live edition must contain two videos")

    required = ["index.html", f"briefs/{date}/index.html", *HISTORICAL_REQUIRED]
    missing = [p for p in required if not (root / p).exists()]
    if missing:
        fail("missing required reader pages: " + ", ".join(missing))

    html_files = list(root.rglob("*.html"))
    joined = "\n".join(read(p) for p in html_files)
    forbidden = [s for s in FORBIDDEN_READER_TEXT if s in joined]
    if forbidden:
        fail("reader-visible internal/test labels remain: " + ", ".join(forbidden))
    if re.search(r'href=["\'][^"\']*command-center', joined, re.I):
        fail("reader exposes a Command Center link")

    home = read(root / "index.html")
    dated = read(root / f"briefs/{date}/index.html")
    if date not in home and edition.get("title", "") not in home:
        # Rendered pages normally use a human-readable date; verify all six current headlines instead.
        if not all(story["headline"] in home for story in edition["stories"]):
            fail("homepage is not the requested live edition")
    if not all(story["headline"] in dated for story in edition["stories"]):
        fail("dated Brief is missing one or more locked stories")
    if dated.count("How useful was this?") < 10:
        fail("live edition rating surfaces are incomplete")
    if "Worth Watching" not in dated or "Worth Listening" not in dated:
        fail("live edition media sections are incomplete")
    if "Add a comment" not in dated and "comments.js" not in dated:
        fail("live edition comment control is not wired")

    watchlist_path = root / "data" / "watchlist.json"
    if not watchlist_path.exists():
        fail("current reader Watchlist data is missing")
    watchlist = json.loads(read(watchlist_path))
    canonical_watchlist = json.loads(Path(args.canonical_watchlist_json).read_text(encoding="utf-8"))
    try:
        counts = validate_public_watchlist(watchlist, canonical_watchlist, date)
    except ValueError as exc:
        fail(str(exc))
    watchlist_page = read(root / "watchlist/index.html")
    if 'data-watchlist-contract="greenfield-watchlist-v1"' not in watchlist_page:
        fail("current Watchlist route is not using the greenfield-owned presentation contract")
    summary_token = f'{counts["new_today"]}-new-{counts["updated_today"]}-updated-{counts["carried_forward"]}-carried'
    if f'data-watchlist-summary="{summary_token}"' not in home:
        fail("homepage Watchlist summary is not bound to the canonical Watchlist counts")

    for story in edition["stories"]:
        route = root / story["permanent_url"].strip("/") / "index.html"
        if not route.exists():
            fail(f"missing live story route: {story['permanent_url']}")
        image = root / story["image"]["path"]
        if not image.exists() or image.stat().st_size == 0:
            fail(f"missing live story image: {story['image']['path']}")

    for slot, suffix in (("general", "general"), ("agents_non_technical_people", "agent-skills")):
        video = edition["worth_watching"][slot]
        if video["status"] != "included":
            fail(f"live video slot not included: {slot}")
        if not (root / "videos" / date / suffix / "index.html").exists():
            fail(f"missing permanent video page: {suffix}")

    for podcast in edition["podcasts"]:
        route = root / podcast["permanent_url"].strip("/") / "index.html"
        if not route.exists():
            fail(f"missing permanent podcast page: {podcast['permanent_url']}")

    archive = read(root / "briefs-archive/index.html")
    if date not in archive and edition.get("title", "") not in archive:
        if not all(story["headline"] in archive for story in edition["stories"]):
            fail("archive does not contain the live edition")

    for feed in ("daily-feed.xml", "feed.xml", "feed.json"):
        path = root / feed
        if not path.exists() or path.stat().st_size == 0:
            fail(f"feed missing or empty: {feed}")

    for asset in ("assets/js/comments.js", "assets/js/feedback.js", "assets/js/share.js"):
        if not (root / asset).exists():
            fail(f"reader interaction asset missing: {asset}")

    build = json.loads(read(root / "build.json"))
    if build.get("historical_cutoff") != "2026-09-23":
        fail("historical parity cutoff changed")
    if build.get("live_edition_date") != date:
        fail("live edition build metadata mismatch")
    if build.get("command_center_included") is not False:
        fail("Command Center exclusion is not proven")

    legacy_hits = []
    for path in html_files:
        if "https://gttome.github.io/Daily-AI-Brief" in read(path):
            legacy_hits.append(str(path.relative_to(root)))
    if legacy_hits:
        fail("legacy canonical reader URLs remain in live candidate: " + ", ".join(legacy_hits[:10]))

    print(json.dumps({
        "result": "passed",
        "edition_date": date,
        "story_count": 6,
        "video_count": 2,
        "podcast_count": 2,
        "historical_cutoff": "2026-09-23",
        "watchlist_counts": counts,
        "watchlist_digest": canonical_watchlist.get("content_digest"),
        "target_url": args.target_url,
        "critical_defects": 0,
        "high_defects": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
