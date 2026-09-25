from __future__ import annotations

import hashlib
import json
import math
import os
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
PROPOSAL_STATUSES = {"Pending review", "Approved", "Rejected"}


class PrivateOwnerDataError(ValueError):
    pass


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _load(path: Path, record_type: str) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "record_type": record_type, "records": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != SCHEMA_VERSION or data.get("record_type") != record_type:
        raise PrivateOwnerDataError(f"unsupported private owner-data file: {path.name}")
    if not isinstance(data.get("records"), list):
        raise PrivateOwnerDataError(f"invalid private owner-data records: {path.name}")
    return data


def _metric(value: Any, name: str) -> Any:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
        raise PrivateOwnerDataError(f"invalid non-negative measurement for {name}")
    return value


def proposal_identity(record: dict[str, Any]) -> str:
    existing = record.get("proposal_id") or record.get("dedupe_id")
    if existing:
        return str(existing)
    core = {
        "edition_date": record.get("edition_date"),
        "item_type": record.get("item_type"),
        "item_id": record.get("item_id"),
        "item_title": record.get("item_title"),
        "target_book": record.get("target_book"),
        "proposed_change": record.get("proposed_change"),
    }
    encoded = json.dumps(core, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "proposal-" + hashlib.sha256(encoded).hexdigest()[:24]


class PrivateOwnerDataStore:
    """Authenticated-owner storage adapter.

    The caller supplies a private filesystem/runtime root. No default repository
    location exists, so private values cannot be written to the public checkout
    accidentally.
    """

    def __init__(self, private_root: Path | str):
        self.root = Path(private_root).expanduser().resolve()
        self.usage_path = self.root / "usage-history.json"
        self.proposals_path = self.root / "book-change-proposals.json"

    def list_usage(self) -> list[dict[str, Any]]:
        return deepcopy(_load(self.usage_path, "usage-history")["records"])

    def upsert_usage(self, record: dict[str, Any]) -> dict[str, Any]:
        attempt_id = str(record.get("attempt_id") or "").strip()
        edition_date = str(record.get("edition_date") or "").strip()
        if not attempt_id or not edition_date:
            raise PrivateOwnerDataError("usage record requires attempt_id and edition_date")
        boundary = str(record.get("measurement_boundary") or "unspecified")
        metrics = {}
        for name, value in (record.get("metrics") or {}).items():
            metrics[str(name)] = _metric(value, str(name))

        payload = _load(self.usage_path, "usage-history")
        rows = payload["records"]
        existing = next((x for x in rows if x.get("attempt_id") == attempt_id), None)
        observation = {
            "measurement_boundary": boundary,
            "metrics": metrics,
            "recorded_at": record.get("recorded_at"),
            "source": record.get("source") or "private-owner-record",
        }
        if existing is None:
            existing = {
                "attempt_id": attempt_id,
                "edition_date": edition_date,
                "observations": [observation],
            }
            rows.append(existing)
        else:
            if existing.get("edition_date") != edition_date:
                raise PrivateOwnerDataError("attempt_id cannot move between editions")
            observations = existing.setdefault("observations", [])
            current = next((x for x in observations if x.get("measurement_boundary") == boundary), None)
            if current is None:
                observations.append(observation)
            else:
                merged = dict(current.get("metrics") or {})
                for name, value in metrics.items():
                    if value is not None:
                        merged[name] = value
                    elif name not in merged:
                        merged[name] = None
                current["metrics"] = merged
                current["recorded_at"] = observation["recorded_at"] or current.get("recorded_at")
                current["source"] = observation["source"]

        _atomic_write(self.usage_path, payload)
        return deepcopy(existing)

    def import_usage(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for record in records:
            self.upsert_usage(record)
        return self.list_usage()

    def list_proposals(self) -> list[dict[str, Any]]:
        return deepcopy(_load(self.proposals_path, "book-change-proposals")["records"])

    def upsert_proposal(self, record: dict[str, Any]) -> dict[str, Any]:
        proposal_id = proposal_identity(record)
        required = ["edition_date", "item_type", "item_title", "target_book", "proposed_change", "evidence_reason"]
        missing = [key for key in required if not str(record.get(key) or "").strip()]
        if missing:
            raise PrivateOwnerDataError("proposal missing required field(s): " + ", ".join(missing))

        payload = _load(self.proposals_path, "book-change-proposals")
        rows = payload["records"]
        existing = next((x for x in rows if x.get("proposal_id") == proposal_id), None)
        requested_status = record.get("status")
        if requested_status is not None and requested_status not in PROPOSAL_STATUSES:
            raise PrivateOwnerDataError("invalid proposal status")

        normalized = {
            "proposal_id": proposal_id,
            "edition_date": record.get("edition_date"),
            "item_type": record.get("item_type"),
            "item_id": record.get("item_id"),
            "item_title": record.get("item_title"),
            "permalink": record.get("permalink"),
            "target_book": record.get("target_book"),
            "proposed_change": record.get("proposed_change"),
            "evidence_reason": record.get("evidence_reason"),
            "teaching_asset": record.get("teaching_asset"),
            "source_evaluation_id": record.get("source_evaluation_id"),
        }
        if existing is None:
            normalized["status"] = requested_status or "Pending review"
            normalized["decision_at"] = record.get("decision_at")
            rows.append(normalized)
            existing = normalized
        else:
            preserved_status = existing.get("status") or "Pending review"
            preserved_decision_at = existing.get("decision_at")
            existing.update({k: v for k, v in normalized.items() if v is not None})
            # Imports/reevaluations never erase an existing owner decision.
            existing["status"] = preserved_status
            existing["decision_at"] = preserved_decision_at

        _atomic_write(self.proposals_path, payload)
        return deepcopy(existing)

    def import_proposals(self, records: list[dict[str, Any]]) -> list[dict[str, Any]]:
        for record in records:
            self.upsert_proposal(record)
        return self.list_proposals()

    def decide_proposal(self, proposal_id: str, status: str, decision_at: str) -> dict[str, Any]:
        if status not in {"Approved", "Rejected", "Pending review"}:
            raise PrivateOwnerDataError("invalid proposal decision")
        payload = _load(self.proposals_path, "book-change-proposals")
        row = next((x for x in payload["records"] if x.get("proposal_id") == proposal_id), None)
        if row is None:
            raise PrivateOwnerDataError("unknown proposal_id")
        row["status"] = status
        row["decision_at"] = decision_at
        _atomic_write(self.proposals_path, payload)
        return deepcopy(row)
