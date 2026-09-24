#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

LEGACY_BASE = "https://gttome.github.io/Daily-AI-Brief"
TEXT_SUFFIXES = {".html", ".xml", ".json", ".js", ".css", ".txt", ".webmanifest"}
ROOT_ROUTE_PREFIXES = (
    "briefs/", "briefs-archive/", "stories/", "videos/", "podcasts/",
    "assets/", "data/", "watchlist/", "about/", "sources/", "subscribe/",
    "daily-feed.xml", "feed.xml", "feed.json", "latest/", "qa/", "trend-radar/"
)


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
    args = ap.parse_args()

    legacy = Path(args.legacy_root)
    dest = Path(args.destination)
    cfg = Path(args.config)
    if not (legacy / "_config.yml").exists():
        raise SystemExit("legacy snapshot is not initialized")
    if not cfg.exists():
        raise SystemExit(f"target config missing: {cfg}")

    shutil.rmtree(dest, ignore_errors=True)
    config_arg = f"{legacy / '_config.yml'},{cfg}"
    subprocess.run(
        ["jekyll", "build", "--source", str(legacy), "--destination", str(dest), "--config", config_arg],
        check=True,
    )

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

    metadata = {
        "schema_version": "1.0.0",
        "target_reader": target_url,
        "base_path": args.base_path,
        "greenfield_source_sha": args.greenfield_sha,
        "legacy_snapshot_sha": args.legacy_sha,
        "historical_cutoff": "2026-09-23",
        "legacy_production_modified": False,
        "command_center_included": False,
        "reader_test_labels_included": False,
    }
    (dest / "build.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(metadata, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
