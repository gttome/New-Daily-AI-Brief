#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

FORBIDDEN_READER_TEXT = (
    "GREENFIELD TEST",
    "PRE-CUTOVER",
    "Representative shadow data",
    "Owner acceptance environment",
    "GREENFIELD COMMAND CENTER",
)
REQUIRED_PAGES = (
    "index.html",
    "briefs-archive/index.html",
    "watchlist/index.html",
    "sources/index.html",
    "about/index.html",
    "subscribe/index.html",
    "briefs/2026-09-23/index.html",
)
SEP23_IMAGES = (
    "01-nemotron-diarization.webp",
    "02-gpt6-sol-luna-copilot.webp",
    "03-copilot-opentelemetry.webp",
    "04-nvidia-confidential-inference.webp",
    "05-copilot-jetbrains-skills.webp",
    "06-agentforce-aws-public-sector.webp",
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def fail(message: str) -> None:
    raise SystemExit(message)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-root", default="_site")
    ap.add_argument("--target-url", default="https://ndaib.gtome.chatgpt.site")
    args = ap.parse_args()
    root = Path(args.site_root)
    if not root.exists():
        fail("reader bundle does not exist")

    missing = [p for p in REQUIRED_PAGES if not (root / p).exists()]
    if missing:
        fail("missing required reader pages: " + ", ".join(missing))

    html_files = list(root.rglob("*.html"))
    joined = "\n".join(read(p) for p in html_files)
    forbidden = [s for s in FORBIDDEN_READER_TEXT if s in joined]
    if forbidden:
        fail("reader-visible test labels remain: " + ", ".join(forbidden))
    if re.search(r'href=["\'][^"\']*command-center', joined, re.I):
        fail("reader exposes a Command Center link")

    home = read(root / "index.html")
    for expected in (
        "Daily Generative AI Brief",
        "September 23, 2026",
        "Copilot for JetBrains adds shared skills",
        "Emerging AI Watchlist",
        "Worth Watching",
        "Worth Listening",
    ):
        if expected not in home:
            fail(f"homepage parity marker missing: {expected}")

    sep23 = read(root / "briefs/2026-09-23/index.html")
    if sep23.count("How useful was this?") < 10:
        fail("September 23 rating surfaces are incomplete")
    if "Add a comment" not in sep23 and "comments.js" not in sep23:
        fail("September 23 comment control is not wired")

    image_dir = root / "briefs" / "images" / "2026-09-23"
    missing_images = [name for name in SEP23_IMAGES if not (image_dir / name).exists()]
    if missing_images:
        fail("September 23 image migration incomplete: " + ", ".join(missing_images))
    for name in SEP23_IMAGES:
        if (image_dir / name).stat().st_size == 0:
            fail(f"empty migrated image: {name}")

    edition_dirs = sorted(
        p.name for p in (root / "briefs").iterdir()
        if p.is_dir() and re.fullmatch(r"2026-\d{2}-\d{2}", p.name) and p.name <= "2026-09-23"
    )
    if "2026-08-17" not in edition_dirs or "2026-09-23" not in edition_dirs or len(edition_dirs) < 38:
        fail(f"historical edition migration incomplete: {len(edition_dirs)} dated editions found")
    if (root / "briefs" / "2026-09-24").exists():
        fail("post-September-23 edition was imported")

    archive = read(root / "briefs-archive/index.html")
    if "221 items" not in archive:
        fail("archive does not expose the reconciled 221-item history")

    for feed in ("daily-feed.xml", "feed.xml", "feed.json"):
        path = root / feed
        if not path.exists() or path.stat().st_size == 0:
            fail(f"feed missing or empty: {feed}")

    comments = read(root / "assets/js/comments.js")
    feedback = read(root / "assets/js/feedback.js")
    share = read(root / "assets/js/share.js")
    if "/api/comments" not in comments or "/api/ratings" not in feedback or "/api/events" not in share:
        fail("reader interaction transports are incomplete")

    build = json.loads(read(root / "build.json"))
    if build.get("command_center_included") is not False:
        fail("build metadata does not prove Command Center exclusion")
    if build.get("historical_cutoff") != "2026-09-23":
        fail("build historical cutoff mismatch")

    legacy_url_hits = []
    for path in html_files:
        if "https://gttome.github.io/Daily-AI-Brief" in read(path):
            legacy_url_hits.append(str(path.relative_to(root)))
    if legacy_url_hits:
        fail("legacy canonical reader URLs remain in final HTML: " + ", ".join(legacy_url_hits[:10]))

    print(json.dumps({
        "result": "passed",
        "dated_editions": len(edition_dirs),
        "html_pages": len(html_files),
        "sep23_images": len(SEP23_IMAGES),
        "target_url": args.target_url,
        "critical_defects": 0,
        "high_defects": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
