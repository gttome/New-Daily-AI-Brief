#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from build_reader_corrections import apply_reader_corrections
from build_reader_runtime import attach_reader_runtime, add_related_coverage

LEGACY_BASE = "https://gttome.github.io/Daily-AI-Brief"
TEXT_SUFFIXES = {".html", ".xml", ".json", ".js", ".css", ".txt", ".webmanifest"}
ROOT_ROUTE_PREFIXES = (
    "briefs/", "briefs-archive/", "stories/", "videos/", "podcasts/",
    "assets/", "data/", "watchlist/", "about/", "sources/", "subscribe/",
    "daily-feed.xml", "feed.xml", "feed.json", "latest/", "qa/", "trend-radar/"
)


WATCHLIST_CONTRACT = "greenfield-watchlist-v1"


def prepare_reader_source(legacy: Path) -> tuple[Path, tempfile.TemporaryDirectory[str] | None]:
    overlay = Path("migration/watchlist-current")
    if not overlay.exists():
        return legacy, None
    tmp = tempfile.TemporaryDirectory(prefix="ndaib-reader-source-")
    source = Path(tmp.name) / "source"
    shutil.copytree(legacy, source)
    for path in overlay.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(overlay)
        dest = source / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    return source, tmp


def annotate_watchlist_contract(dest: Path) -> None:
    data_path = dest / "data" / "watchlist.json"
    if not data_path.exists():
        return
    data = json.loads(data_path.read_text(encoding="utf-8"))
    counts = data.get("counts") or {}
    token = (
        f"{int(counts.get('new_today') or 0)}-new-"
        f"{int(counts.get('updated_today') or 0)}-updated-"
        f"{int(counts.get('carried_forward') or 0)}-carried"
    )
    watch = dest / "watchlist" / "index.html"
    if watch.exists():
        text = watch.read_text(encoding="utf-8")
        if 'data-watchlist-contract="' not in text:
            text = text.replace(
                'id="watchlist-root"',
                f'id="watchlist-root" data-watchlist-contract="{WATCHLIST_CONTRACT}"',
                1,
            )
        watch.write_text(text, encoding="utf-8")
    home = dest / "index.html"
    if home.exists():
        text = home.read_text(encoding="utf-8")
        text = text.replace(
            'data-watchlist-preview=""',
            f'data-watchlist-preview="" data-watchlist-contract="{WATCHLIST_CONTRACT}" data-watchlist-summary="{token}"',
            1,
        )
        home.write_text(text, encoding="utf-8")


def rewrite_root_routes(text: str, base_path: str) -> str:
    base = "/" + base_path.strip("/") if base_path.strip("/") else ""
    if not base:
        return text
    for prefix in ROOT_ROUTE_PREFIXES:
        text = text.replace(f'"/{prefix}', f'"{base}/{prefix}')
        text = text.replace(f"\'/{prefix}", f"\'{base}/{prefix}")
        text = text.replace(f'href="/{prefix}', f'href="{base}/{prefix}')
        text = text.replace(f'src="/{prefix}', f'src="{base}/{prefix}')
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--legacy-root", default="legacy_snapshot")
    ap.add_argument("--destination", default="_site")
    ap.add_argument("--config", default="migration/ndaib-jekyll.yml")
    ap.add_argument("--site-url", default="https://ndaib.gtome.chatgpt.site")
    ap.add_argument("--base-path", default="")
    ap.add_argument("--greenfield-sha", default=os.environ.get("GITHUB_SHA", "local"))
    ap.add_argument("--legacy-sha", default="4ac06268048a3241d2ecaa5ce7c2638266500d75")
    ap.add_argument("--live-edition-date", default="")
    args = ap.parse_args()

    legacy = Path(args.legacy_root)
    dest = Path(args.destination)
    cfg = Path(args.config)
    if not (legacy / "_config.yml").exists():
        raise SystemExit("legacy snapshot is not initialized")
    if not cfg.exists():
        raise SystemExit(f"target config missing: {cfg}")

    shutil.rmtree(dest, ignore_errors=True)
    source, source_tmp = prepare_reader_source(legacy)
    config_arg = f"{source / '_config.yml'},{cfg}"
    try:
        subprocess.run(
            ["jekyll", "build", "--source", str(source), "--destination", str(dest), "--config", config_arg],
            check=True,
        )
    finally:
        if source_tmp is not None:
            source_tmp.cleanup()

    target_url = args.site_url.rstrip("/")
    for path in dest.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        original = text
        text = text.replace(LEGACY_BASE, target_url)
        text = rewrite_root_routes(text, args.base_path)
        if text != original:
            path.write_text(text, encoding="utf-8")

    corrections = apply_reader_corrections(dest, legacy)
    add_related_coverage(dest, legacy)
    annotate_watchlist_contract(dest)
    corrections['reader_runtime'] = attach_reader_runtime(dest, legacy)
    (dest / "reader-corrections.json").write_text(json.dumps(corrections, indent=2) + "\n", encoding="utf-8")

    metadata = {
        "schema_version": "1.0.0",
        "target_reader": target_url,
        "base_path": args.base_path,
        "greenfield_source_sha": args.greenfield_sha,
        "legacy_snapshot_sha": args.legacy_sha,
        "historical_cutoff": "2026-09-23",
        "live_edition_date": args.live_edition_date or None,
        "legacy_production_modified": False,
        "command_center_included": False,
        "reader_test_labels_included": False,
    }
    (dest / "build.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
