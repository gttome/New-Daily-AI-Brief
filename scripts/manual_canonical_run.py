#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from new_daily_ai_brief import start_daily_brief


def main() -> int:
    ap = argparse.ArgumentParser(description="Authorized manual adapter to the canonical greenfield RunEngine")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--input-root", required=True)
    ap.add_argument("--state-root", default=".state/manual")
    ap.add_argument("--owner", default="authorized-manual-workflow")
    ap.add_argument(
        "--editorial-only",
        action="store_true",
        help="Lock live discovery/editorial state only; do not fabricate media, images, or publication.",
    )
    args = ap.parse_args()

    root = Path(args.input_root)
    required = (root / "editorial",) if args.editorial_only else (
        root / "editorial",
        root / "build",
        root / "pre_release",
    )
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit("prepared input package is incomplete: " + ", ".join(missing))

    kwargs = {
        "edition_date": args.edition_date,
        "mode": "production",
        "state_root": Path(args.state_root),
        "owner": args.owner,
        "editorial_fixture_root": root / "editorial",
        "editorial_only": args.editorial_only,
    }
    if not args.editorial_only:
        kwargs.update({
            "build_fixture_root": root / "build",
            "pre_release_fixture_root": root / "pre_release",
        })

    run = start_daily_brief(**kwargs)
    result = {
        "run_id": run["run_id"],
        "edition_date": run["edition_date"],
        "mode": run["mode"],
        "current_state": run["current_state"],
        "completion_status": run.get("completion_status"),
        "incident_count": run.get("incident_count"),
        "anti_rework": run.get("anti_rework"),
        "canonical_entry_point": "start_daily_brief(date, mode)",
        "run_depth": "editorial_locked" if args.editorial_only else "complete",
    }
    print(json.dumps(result, indent=2, sort_keys=True))

    if args.editorial_only:
        return 0 if (
            result["current_state"] == "Building"
            and result["completion_status"] == "editorial_locked"
        ) else 2
    return 0 if result["current_state"] == "Complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
