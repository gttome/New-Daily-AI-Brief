#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REPO_PATH_RE = re.compile(r"`((?:docs|evidence|schemas|fixtures|src|tests|scripts|\.github)/[^\`\s]+)`")
MUTABLE_TOP_LEVEL = {"repository_closure_status", "closure"}


class ValidationError(RuntimeError):
    pass


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValidationError(f"invalid JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON root must be an object: {path}")
    return value


def git_show_json(base_ref: str, rel: str) -> dict[str, Any] | None:
    if not base_ref:
        return None
    proc = subprocess.run(
        ["git", "show", f"{base_ref}:{rel}"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if proc.returncode != 0:
        return None
    try:
        value = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise ValidationError(f"base JSON is invalid for {rel}") from exc
    return value if isinstance(value, dict) else None


def stripped_immutable(value: dict[str, Any], readiness_key: str | None) -> dict[str, Any]:
    clone = dict(value)
    for key in MUTABLE_TOP_LEVEL:
        clone.pop(key, None)
    if readiness_key:
        clone.pop(readiness_key, None)
    return clone


def validate_references(path: Path) -> None:
    if path.suffix.lower() != ".md":
        return
    text = path.read_text(encoding="utf-8")
    for rel in REPO_PATH_RE.findall(text):
        rel = rel.rstrip(".,;:)")
        if "*" in rel or "{" in rel:
            continue
        if not (ROOT / rel).exists():
            raise ValidationError(f"missing repository reference {rel} in {path.relative_to(ROOT)}")


def validate_progress(data: dict[str, Any], path: Path) -> None:
    if data.get("record_type") != "iteration-progress":
        return
    required = {
        "schema_version", "record_type", "iteration", "phase", "branch",
        "checkpoint_head_sha", "completed_gates", "active_gate", "ci_runs",
        "closure_state", "next_permissible_action", "resume_policy",
    }
    missing = sorted(required - set(data))
    if missing:
        raise ValidationError(f"progress record missing {missing}: {path}")
    if data.get("schema_version") != "1.0.0":
        raise ValidationError(f"unsupported progress schema: {path}")
    sha = data.get("checkpoint_head_sha")
    if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValidationError(f"progress checkpoint_head_sha must be an exact SHA: {path}")
    if not isinstance(data.get("completed_gates"), list):
        raise ValidationError(f"progress completed_gates must be a list: {path}")
    if data.get("closure_state") not in {
        "not_started", "implementation_verified", "closure_package",
        "closure_verification", "reconciliation", "final_main_verification", "complete"
    }:
        raise ValidationError(f"unsupported closure_state: {path}")
    resume = data.get("resume_policy") or {}
    for key in (
        "reuse_existing_pr", "reuse_exact_head_ci", "reuse_merged_commits",
        "reuse_closure_artifacts", "duplicate_pr_permitted",
        "duplicate_ci_for_same_head_permitted", "prior_iteration_rebuild_permitted",
    ):
        if key not in resume:
            raise ValidationError(f"progress resume_policy missing {key}: {path}")
    if resume["duplicate_pr_permitted"] is not False:
        raise ValidationError(f"progress must forbid duplicate PRs: {path}")
    if resume["duplicate_ci_for_same_head_permitted"] is not False:
        raise ValidationError(f"progress must forbid duplicate exact-head CI: {path}")
    if resume["prior_iteration_rebuild_permitted"] is not False:
        raise ValidationError(f"progress must forbid prior-iteration rebuild: {path}")


def validate_closure(data: dict[str, Any], path: Path, base_ref: str) -> None:
    iteration = data.get("iteration")
    closure = data.get("closure")
    if not isinstance(iteration, int) or not isinstance(closure, dict):
        return
    readiness_key = f"iteration{iteration + 1}_ready"
    top_status = data.get("repository_closure_status")
    closure_status = closure.get("repository_closure_status")
    top_ready = data.get(readiness_key)
    closure_ready = closure.get(readiness_key)
    if top_status is not None and closure_status is not None and top_status != closure_status:
        raise ValidationError(f"closure status mismatch: {path}")
    if top_ready is not None and closure_ready is not None and top_ready != closure_ready:
        raise ValidationError(f"next-iteration readiness mismatch: {path}")
    status = closure_status if closure_status is not None else top_status
    ready = closure_ready if closure_ready is not None else top_ready
    if status == "complete" and ready is not True:
        raise ValidationError(f"complete closure must set {readiness_key}=true: {path}")
    if status == "pending" and ready is True:
        raise ValidationError(f"pending closure cannot set {readiness_key}=true: {path}")
    required_paths = closure.get("required_paths") or []
    if required_paths and not isinstance(required_paths, list):
        raise ValidationError(f"closure required_paths must be a list: {path}")
    for rel in required_paths:
        if not isinstance(rel, str) or not (ROOT / rel).exists():
            raise ValidationError(f"required closure path missing: {rel!r} from {path}")
    base = git_show_json(base_ref, str(path.relative_to(ROOT)))
    if base is not None:
        base_iteration = base.get("iteration")
        if base_iteration != iteration:
            raise ValidationError(f"iteration identity changed in metadata-only update: {path}")
        if stripped_immutable(base, readiness_key) != stripped_immutable(data, readiness_key):
            raise ValidationError(
                f"metadata-only closure update changed immutable implementation evidence: {path}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--changed-file-list", required=True)
    parser.add_argument("--base-ref", default="")
    args = parser.parse_args()
    changed = [
        line.strip()
        for line in (ROOT / args.changed_file_list).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not changed:
        raise ValidationError("bounded closure validation received no changed files")
    for rel in changed:
        if not (rel.startswith("docs/") or rel.startswith("evidence/")):
            raise ValidationError(f"bounded closure validation received executable/contract path: {rel}")
        path = ROOT / rel
        if not path.exists():
            continue
        if path.suffix.lower() == ".json":
            data = read_json(path)
            validate_progress(data, path)
            validate_closure(data, path, args.base_ref)
        elif path.suffix.lower() == ".md":
            validate_references(path)
        else:
            raise ValidationError(f"unsupported bounded metadata file type: {rel}")
    print(f"bounded closure metadata validation passed for {len(changed)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
