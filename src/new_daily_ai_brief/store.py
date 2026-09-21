from __future__ import annotations

import hashlib
import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .contracts import ARTIFACT_DEPENDENCIES, ARTIFACT_FILES, RUN_SCHEMA_VERSION, SCHEMA_VERSION


class ContractError(RuntimeError):
    pass


class LeaseCollision(ContractError):
    pass


class LockedArtifactMutation(ContractError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def semantic_digest(record: dict[str, Any]) -> str:
    body = deepcopy(record)
    for key in ("content_digest", "created_at", "updated_at", "locked_at", "invalidated_at"):
        body.pop(key, None)
    return digest(body)


class CanonicalStore:
    """Small file-backed canonical store for Iteration 1.

    One directory is authoritative for one edition/mode run. JSON files are written
    atomically. No chat/session information is needed to resume.
    """

    def __init__(self, root: Path, edition_date: str, mode: str):
        self.root = Path(root)
        self.run_dir = self.root / f"{edition_date}__{mode}"
        self.run_dir.mkdir(parents=True, exist_ok=True)
        self.edition_date = edition_date
        self.mode = mode

    @property
    def run_path(self) -> Path:
        return self.run_dir / "run.json"

    @property
    def lease_path(self) -> Path:
        return self.run_dir / "lease.json"

    @property
    def incident_path(self) -> Path:
        return self.run_dir / "incident.json"

    def artifact_path(self, artifact_type: str) -> Path:
        return self.run_dir / ARTIFACT_FILES[artifact_type]

    def _atomic_write(self, path: Path, value: dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp, path)

    def read_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write_run(self, run: dict[str, Any]) -> None:
        run["updated_at"] = utc_now()
        self._atomic_write(self.run_path, run)

    def load_run(self) -> dict[str, Any] | None:
        record = self.read_json(self.run_path)
        if record is None:
            return None
        return self.migrate_run(record)

    def migrate_run(self, record: dict[str, Any]) -> dict[str, Any]:
        version = record.get("schema_version")
        if version == RUN_SCHEMA_VERSION:
            return record
        if version == "0.9.0":
            migrated = deepcopy(record)
            migrated["schema_version"] = RUN_SCHEMA_VERSION
            migrated.setdefault("anti_rework", {
                "locked_stage_reexecutions": 0,
                "full_pipeline_restarts": 0,
                "artifact_reuses": 0,
                "artifact_rebuilds": 0,
            })
            migrated.setdefault("stage_executions", {})
            migrated.setdefault("stage_receipts", {})
            migrated.setdefault("recovery_target", None)
            return migrated
        raise ContractError(f"unsupported run schema version: {version!r}")

    def acquire_lease(self, run_id: str, owner: str) -> dict[str, Any]:
        existing = self.read_json(self.lease_path)
        if existing and existing.get("active"):
            if existing.get("run_id") == run_id and existing.get("owner") == owner:
                return existing
            raise LeaseCollision(f"active lease owned by {existing.get('owner')}")
        lease = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "owner": owner,
            "active": True,
            "acquired_at": utc_now(),
        }
        self._atomic_write(self.lease_path, lease)
        return lease

    def release_lease(self, owner: str) -> None:
        lease = self.read_json(self.lease_path)
        if not lease:
            return
        if lease.get("owner") != owner:
            raise LeaseCollision("cannot release another owner's lease")
        lease["active"] = False
        lease["released_at"] = utc_now()
        self._atomic_write(self.lease_path, lease)

    def load_artifact(self, artifact_type: str) -> dict[str, Any] | None:
        return self.read_json(self.artifact_path(artifact_type))

    def lock_artifact(
        self,
        artifact_type: str,
        artifact_id: str,
        data: dict[str, Any],
        produced_by_stage: str,
        input_digests: Iterable[str],
    ) -> tuple[dict[str, Any], bool]:
        path = self.artifact_path(artifact_type)
        existing = self.read_json(path)
        record = {
            "artifact_id": artifact_id,
            "artifact_type": artifact_type,
            "schema_version": SCHEMA_VERSION,
            "edition_date": self.edition_date,
            "mode": self.mode,
            "produced_by_stage": produced_by_stage,
            "input_digests": sorted(input_digests),
            "status": "locked",
            "data": data,
        }
        record["content_digest"] = semantic_digest(record)
        if existing and existing.get("status") == "locked":
            if existing.get("content_digest") == record["content_digest"]:
                return existing, True
            raise LockedArtifactMutation(
                f"{artifact_type} is locked; explicit dependency invalidation is required"
            )
        now = utc_now()
        record["created_at"] = existing.get("created_at", now) if existing else now
        record["locked_at"] = now
        self._atomic_write(path, record)
        return record, False

    def descendants(self, artifact_type: str) -> set[str]:
        result: set[str] = set()
        frontier = [artifact_type]
        while frontier:
            current = frontier.pop()
            for child, deps in ARTIFACT_DEPENDENCIES.items():
                if current in deps and child not in result:
                    result.add(child)
                    frontier.append(child)
        return result

    def invalidate(self, artifact_type: str, reason: str) -> list[str]:
        targets = [artifact_type, *sorted(self.descendants(artifact_type))]
        changed: list[str] = []
        for target in targets:
            record = self.load_artifact(target)
            if not record or record.get("status") != "locked":
                continue
            record["status"] = "invalidated"
            record["invalidated_at"] = utc_now()
            record["invalidation_reason"] = reason
            self._atomic_write(self.artifact_path(target), record)
            changed.append(target)
        return changed

    def write_incident(self, incident: dict[str, Any]) -> None:
        self._atomic_write(self.incident_path, incident)

    def load_incident(self) -> dict[str, Any] | None:
        return self.read_json(self.incident_path)
