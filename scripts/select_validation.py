#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any


class UnmappedPathError(RuntimeError):
    pass


def _matches(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(path, pattern) for pattern in patterns)


def classify_paths(impact_map: dict[str, Any], changed_paths: list[str]) -> dict[str, Any]:
    paths = [p.strip().replace("\\\\", "/") for p in changed_paths if p.strip()]
    if not paths:
        raise UnmappedPathError("No changed paths were supplied; refusing to infer an empty validation scope.")

    components = impact_map["components"]
    path_components: dict[str, list[str]] = {}
    direct_components: list[str] = []
    unknown: list[str] = []

    for path in paths:
        matched = [name for name, cfg in components.items() if _matches(path, cfg.get("paths", []))]
        if not matched:
            unknown.append(path)
            continue
        path_components[path] = matched
        for name in matched:
            if name not in direct_components:
                direct_components.append(name)

    if unknown:
        raise UnmappedPathError(
            "Unmapped material path(s): " + ", ".join(unknown)
            + ". Update config/test-impact-map.json before validation can pass."
        )

    nonexclusive = [name for name in direct_components if not components[name].get("only_when_exclusive")]
    active_direct = [
        name for name in direct_components
        if not (components[name].get("only_when_exclusive") and nonexclusive)
    ]

    dependency_components: list[str] = []
    for name in active_direct:
        for dep in components[name].get("dependencies", []):
            if dep not in active_direct and dep not in dependency_components:
                dependency_components.append(dep)

    development: list[str] = []
    integration: list[str] = []
    rationale: list[dict[str, Any]] = []

    for name in active_direct:
        cfg = components[name]
        for suite in cfg.get("development_suites", []):
            if suite not in development:
                development.append(suite)
        for suite in cfg.get("integration_suites", []):
            if suite not in integration:
                integration.append(suite)
        rationale.append({
            "component": name,
            "role": "direct",
            "reason": cfg.get("rationale", ""),
            "development_suites": cfg.get("development_suites", []),
            "integration_suites": cfg.get("integration_suites", []),
        })

    for name in dependency_components:
        cfg = components[name]
        for suite in cfg.get("development_suites", []):
            if suite not in development:
                development.append(suite)
        rationale.append({
            "component": name,
            "role": "immediate_dependency",
            "reason": cfg.get("rationale", ""),
            "development_suites": cfg.get("development_suites", []),
            "integration_suites": [],
        })

    recommend_full = any(components[name].get("recommend_full_system_validation", False) for name in active_direct)
    return {
        "schema_version": "1.0",
        "impact_map_version": impact_map.get("schema_version"),
        "changed_paths": paths,
        "path_components": path_components,
        "direct_components": active_direct,
        "dependency_components": dependency_components,
        "development_suites": development,
        "integration_suites": integration,
        "full_system_validation_requested": False,
        "full_system_validation_recommended": recommend_full,
        "full_system_validation_workflow": impact_map["full_system_validation"]["workflow"],
        "rationale": rationale,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--map", dest="map_path", default="config/test-impact-map.json")
    parser.add_argument("--changed-file-list", required=True)
    parser.add_argument("--output", default="validation-selection.json")
    args = parser.parse_args()

    impact_map = json.loads(Path(args.map_path).read_text(encoding="utf-8"))
    changed_paths = Path(args.changed_file_list).read_text(encoding="utf-8").splitlines()
    try:
        selection = classify_paths(impact_map, changed_paths)
    except UnmappedPathError as exc:
        print(f"VALIDATION ROUTING FAIL-CLOSED: {exc}")
        return 2

    Path(args.output).write_text(json.dumps(selection, indent=2) + "\n", encoding="utf-8")
    print("Validation scope:")
    print(json.dumps(selection, indent=2))
    print("Full System Validation: NOT REQUESTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
