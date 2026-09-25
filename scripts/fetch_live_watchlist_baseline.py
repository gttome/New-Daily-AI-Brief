#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import date, timedelta
from pathlib import Path
from urllib.request import Request, urlopen


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Resolve the prior reader-bound Watchlist baseline")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--url", default="https://ndaib.gtome.chatgpt.site/data/watchlist.json")
    ap.add_argument("--fallback", default="legacy_snapshot/_data/watchlist.json")
    args = ap.parse_args()

    edition = date.fromisoformat(args.edition_date)
    prior = None
    source = None
    try:
        req = Request(args.url, headers={"User-Agent": "New-Daily-AI-Brief-Watchlist/1.0"})
        with urlopen(req, timeout=20) as response:
            prior = json.loads(response.read().decode("utf-8"))
        source = args.url
    except Exception as exc:
        fallback = Path(args.fallback)
        if not fallback.is_file():
            raise SystemExit(f"live Watchlist baseline unavailable and fallback missing: {exc}")
        prior = load(fallback)
        source = str(fallback)

    prior_date = date.fromisoformat(str(prior.get("edition_date") or ""))
    if prior_date >= edition:
        raise SystemExit("Watchlist baseline must predate the requested edition")
    if source != args.url and prior_date != edition - timedelta(days=1):
        raise SystemExit(
            f"fallback Watchlist is stale ({prior_date}); refusing to use it for {edition}. "
            "A current reader-bound baseline is required."
        )

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(prior, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"edition_date": args.edition_date, "baseline_date": str(prior_date), "source": source}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
