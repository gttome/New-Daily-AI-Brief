#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_DOMAINS = set("ABCDEFGHIJ")
REQUIRED_FIELDS = {
    "domain", "data_family", "current_source", "current_private_or_public",
    "new_authoritative_source", "new_command_center_destination",
    "historical_requirement", "status", "validation_method", "notes",
    "last_reviewed_at",
}
ALLOWED = {"equivalent", "improved", "deliberately_retired", "not_yet_implemented"}
PRIVATE_FAMILIES = {
    "usage_recorded_production_effort",
    "book_change_proposals_owner_decisions",
    "private_comments_annotations",
}
PUBLIC_FORBIDDEN_PRIVATE_KEYS = {
    "private_usage_records", "usage_history_records", "book_change_proposals",
    "proposal_records_private", "owner_annotations",
}


def gitlink(path: str) -> str | None:
    try:
        out = subprocess.check_output(
            ["git", "ls-tree", "HEAD", path], cwd=ROOT, text=True
        ).strip()
    except Exception:
        return None
    parts = out.split()
    return parts[2] if len(parts) >= 3 and parts[1] == "commit" else None


def walk_keys(value: Any):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key
            yield from walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_keys(child)


def validate(matrix_path: Path, state_path: Path) -> dict[str, Any]:
    matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    rows = matrix.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValueError("parity matrix must contain rows")

    seen = set()
    domains = set()
    counts = {status: 0 for status in ALLOWED}
    private_seen = set()
    for row in rows:
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise ValueError(f"matrix row missing fields: {sorted(missing)}")
        key = (row["domain"], row["data_family"])
        if key in seen:
            raise ValueError(f"duplicate parity row: {key}")
        seen.add(key)
        domains.add(row["domain"])
        if row["status"] not in ALLOWED:
            raise ValueError(f"invalid parity status: {row['status']}")
        counts[row["status"]] += 1
        if row["status"] == "not_yet_implemented":
            raise ValueError(f"unresolved parity gap: {row['data_family']}")
        if row["status"] == "deliberately_retired":
            approvals = matrix.get("deliberate_retirements") or []
            if not any(x.get("data_family") == row["data_family"] and x.get("owner_approved") is True for x in approvals):
                raise ValueError(f"unapproved deliberate retirement: {row['data_family']}")
        if row["data_family"] in PRIVATE_FAMILIES:
            private_seen.add(row["data_family"])
            if row["current_private_or_public"] != "private":
                raise ValueError(f"private family misclassified: {row['data_family']}")
            combined = (str(row["new_authoritative_source"]) + " " + str(row["new_command_center_destination"])).lower()
            if "private" not in combined and "authenticated" not in combined:
                raise ValueError(f"private family lacks authenticated/private destination: {row['data_family']}")

    if domains != REQUIRED_DOMAINS:
        raise ValueError(f"parity domains incomplete: expected {sorted(REQUIRED_DOMAINS)}, got {sorted(domains)}")
    if private_seen != PRIVATE_FAMILIES:
        raise ValueError("private owner-data families incomplete")

    expected_legacy = matrix.get("legacy_reference_sha")
    actual_legacy = gitlink("legacy_snapshot")
    if actual_legacy and expected_legacy != actual_legacy:
        raise ValueError(f"legacy snapshot mismatch: matrix={expected_legacy} gitlink={actual_legacy}")

    state = json.loads(state_path.read_text(encoding="utf-8"))
    state_keys = set(walk_keys(state))
    leaked = sorted(PUBLIC_FORBIDDEN_PRIVATE_KEYS.intersection(state_keys))
    if leaked:
        raise ValueError(f"private owner-data leaked into committed public state: {leaked}")
    parity = state.get("data_parity") or {}
    if parity.get("matrix_version") != matrix.get("matrix_version"):
        raise ValueError("committed Command Center state does not bind current parity matrix version")
    if parity.get("unresolved_required_families") != 0:
        raise ValueError("committed Command Center state reports unresolved required families")
    if parity.get("privacy_leakage_defects") != 0:
        raise ValueError("committed Command Center state reports privacy leakage")

    result = {
        "validation": "Command Center Data Parity Validation",
        "result": "PASS",
        "matrix_version": matrix.get("matrix_version"),
        "row_count": len(rows),
        "domains": sorted(domains),
        "status_counts": counts,
        "legacy_reference_sha": expected_legacy,
        "private_families": sorted(private_seen),
        "unresolved_required_families": 0,
        "privacy_leakage_defects": 0,
        "full_system_validation": "NOT REQUESTED",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--matrix", default="config/command-center-data-parity.json")
    parser.add_argument("--state", default="site/command-center/state.json")
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        result = validate(ROOT / args.matrix, ROOT / args.state)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({
            "validation": "Command Center Data Parity Validation",
            "result": "FAIL",
            "error": str(exc),
            "full_system_validation": "NOT REQUESTED",
        }, indent=2))
        return 1
    if args.output:
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
