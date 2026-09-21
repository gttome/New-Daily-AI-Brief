from __future__ import annotations

import argparse
import json
from pathlib import Path

from .contracts import FailureInjection
from .engine import SyntheticFailure, start_daily_brief


def main() -> int:
    parser = argparse.ArgumentParser(description="New Daily AI Brief Iteration 1 run engine")
    sub = parser.add_subparsers(dest="command", required=True)
    run_now = sub.add_parser("run-now", help="Run the canonical orchestrator entry point")
    run_now.add_argument("--date", required=True)
    run_now.add_argument("--mode", choices=["synthetic", "shadow"], default="synthetic")
    run_now.add_argument("--state-dir", default=".state")
    run_now.add_argument("--inject-failure", choices=["Validating"], default=None)
    args = parser.parse_args()

    injection = FailureInjection(args.inject_failure) if args.inject_failure else None
    try:
        run = start_daily_brief(
            edition_date=args.date,
            mode=args.mode,
            state_root=Path(args.state_dir),
            failure_injection=injection,
        )
    except SyntheticFailure as exc:
        print(json.dumps({"result": "injected_failure", "failure": str(exc)}, indent=2))
        return 2
    print(json.dumps(run, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
