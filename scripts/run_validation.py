#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def _sha() -> str:
    if os.environ.get("GITHUB_SHA"):
        return os.environ["GITHUB_SHA"]
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _run(command: list[str]) -> tuple[int, float]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = str(ROOT / "src") + (os.pathsep + existing if existing else "")
    started = time.monotonic()
    proc = subprocess.run(command, cwd=ROOT, env=env, text=True)
    return proc.returncode, time.monotonic() - started


def _commands(cfg: dict[str, Any], selection: dict[str, Any]) -> list[list[str]]:
    kind = cfg.get("kind")
    if kind == "changed-tests":
        return [[sys.executable, path, "-v"] for path in selection["changed_paths"] if path.startswith("tests/") and path.endswith(".py")]
    if kind == "closure-metadata":
        handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
        with handle:
            handle.write("\n".join(selection["changed_paths"]) + "\n")
        return [[sys.executable, "scripts/validate_closure_metadata.py", "--changed-file-list", handle.name, "--base-ref", ""]]
    command = [sys.executable if token == "{python}" else token for token in cfg.get("command", [])]
    return [command] if command else []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", dest="map_path", default="config/test-impact-map.json")
    parser.add_argument("--selection", default="validation-selection.json")
    parser.add_argument("--evidence", default="validation-evidence.json")
    args = parser.parse_args()

    impact_map = json.loads(Path(args.map_path).read_text(encoding="utf-8"))
    selection = json.loads(Path(args.selection).read_text(encoding="utf-8"))
    suites_cfg = impact_map["suites"]

    development = selection.get("development_suites", [])
    integration = selection.get("integration_suites", [])
    ordered: list[str] = []
    for suite in development + integration:
        if suite not in ordered:
            ordered.append(suite)

    started_at = dt.datetime.now(dt.timezone.utc)
    results: list[dict[str, Any]] = []
    failed = False

    for suite_id in ordered:
        cfg = suites_cfg.get(suite_id)
        if cfg is None:
            raise SystemExit(f"Selected suite {suite_id!r} is missing from test-impact-map.json")
        if cfg.get("requires_submodules"):
            code, elapsed = _run(["git", "submodule", "update", "--init", "--recursive"])
            if code != 0:
                results.append({"suite": suite_id, "levels": [], "result": "FAIL", "elapsed_seconds": round(elapsed, 3), "description": "Submodule initialization failed."})
                failed = True
                continue

        suite_elapsed = 0.0
        suite_failed = False
        commands = _commands(cfg, selection)
        for command in commands:
            print("$ " + " ".join(command))
            code, elapsed = _run(command)
            suite_elapsed += elapsed
            if code != 0:
                suite_failed = True
        result = "FAIL" if suite_failed else "PASS"
        failed = failed or suite_failed
        results.append({
            "suite": suite_id,
            "levels": [level for level, ids in (("development", development), ("integration", integration)) if suite_id in ids],
            "result": result,
            "elapsed_seconds": round(suite_elapsed, 3),
            "description": cfg.get("description", ""),
            "note": "No changed Python test required execution." if not commands and cfg.get("kind") == "changed-tests" else "",
        })

    ended_at = dt.datetime.now(dt.timezone.utc)
    dev_fail = any(r["result"] == "FAIL" and "development" in r.get("levels", []) for r in results)
    int_fail = any(r["result"] == "FAIL" and "integration" in r.get("levels", []) for r in results)
    evidence = {
        "schema_version": "1.0",
        "tested_sha": _sha(),
        "start_time_utc": started_at.isoformat(),
        "end_time_utc": ended_at.isoformat(),
        "elapsed_seconds": round((ended_at - started_at).total_seconds(), 3),
        "selection": selection,
        "suite_results": results,
        "Development Validation": "FAIL" if dev_fail else "PASS",
        "Integration Validation": "FAIL" if int_fail else "PASS",
        "Full System Validation": "NOT REQUESTED",
        "overall_result": "FAIL" if failed else "PASS",
    }
    Path(args.evidence).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(evidence, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
