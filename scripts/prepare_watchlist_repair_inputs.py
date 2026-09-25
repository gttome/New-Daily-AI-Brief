#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from new_daily_ai_brief.watchlist_live import prepare_watchlist_inputs


def load(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise SystemExit(f"required file missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Prepare only repaired Watchlist Build-stage inputs")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--baseline-json", required=True)
    ap.add_argument("--review-json", required=True)
    ap.add_argument("--build-root", required=True)
    args = ap.parse_args()

    prior = load(Path(args.baseline_json))
    review = load(Path(args.review_json))
    registry, catalog, manifest = prepare_watchlist_inputs(args.edition_date, prior, review)
    root = Path(args.build_root)
    dump(root / "watchlist-registry.json", registry)
    dump(root / "watchlist-catalog.json", catalog)
    dump(root / "watchlist-repair-manifest.json", manifest)
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
