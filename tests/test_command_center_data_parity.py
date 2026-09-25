from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from new_daily_ai_brief.command_center_private import (  # noqa: E402
    PrivateOwnerDataError,
    PrivateOwnerDataStore,
)


class CommandCenterDataParityTests(unittest.TestCase):
    def test_dedicated_parity_validator_passes(self):
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "validate_command_center_data_parity.py")],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["result"], "PASS")
        self.assertEqual(payload["domains"], list("ABCDEFGHIJ"))
        self.assertEqual(payload["unresolved_required_families"], 0)
        self.assertEqual(payload["privacy_leakage_defects"], 0)
        self.assertEqual(payload["full_system_validation"], "NOT REQUESTED")

    def test_usage_history_preserves_zero_missing_and_boundaries(self):
        with tempfile.TemporaryDirectory() as td:
            store = PrivateOwnerDataStore(td)
            store.upsert_usage({
                "attempt_id": "attempt-1",
                "edition_date": "2026-09-24",
                "measurement_boundary": "publication",
                "metrics": {"work_credits": 0, "elapsed_seconds": 120, "image_rejects": None},
            })
            store.upsert_usage({
                "attempt_id": "attempt-1",
                "edition_date": "2026-09-24",
                "measurement_boundary": "publication",
                "metrics": {"elapsed_seconds": 121, "image_rejects": None},
            })
            store.upsert_usage({
                "attempt_id": "attempt-1",
                "edition_date": "2026-09-24",
                "measurement_boundary": "validation",
                "metrics": {"elapsed_seconds": 30},
            })
            rows = store.list_usage()
            self.assertEqual(len(rows), 1)
            observations = rows[0]["observations"]
            self.assertEqual(len(observations), 2)
            publication = next(x for x in observations if x["measurement_boundary"] == "publication")
            self.assertEqual(publication["metrics"]["work_credits"], 0)
            self.assertEqual(publication["metrics"]["elapsed_seconds"], 121)
            self.assertIsNone(publication["metrics"]["image_rejects"])

    def test_usage_history_rejects_invalid_measurement_without_suppressing_others(self):
        with tempfile.TemporaryDirectory() as td:
            store = PrivateOwnerDataStore(td)
            store.upsert_usage({
                "attempt_id": "attempt-good",
                "edition_date": "2026-09-24",
                "metrics": {"elapsed_seconds": 10},
            })
            with self.assertRaises(PrivateOwnerDataError):
                store.upsert_usage({
                    "attempt_id": "attempt-bad",
                    "edition_date": "2026-09-24",
                    "metrics": {"elapsed_seconds": -1},
                })
            self.assertEqual([x["attempt_id"] for x in store.list_usage()], ["attempt-good"])

    def test_book_proposal_import_is_idempotent_and_preserves_owner_decision(self):
        record = {
            "edition_date": "2026-09-24",
            "item_type": "article",
            "item_id": "story-1",
            "item_title": "Example",
            "target_book": "Generative AI Professional Series",
            "proposed_change": "Add a short worked example.",
            "evidence_reason": "The completed Brief item adds a material implementation pattern.",
        }
        with tempfile.TemporaryDirectory() as td:
            store = PrivateOwnerDataStore(td)
            first = store.upsert_proposal(record)
            self.assertEqual(first["status"], "Pending review")
            store.decide_proposal(first["proposal_id"], "Approved", "2026-09-24T20:00:00-05:00")
            store.import_proposals([record, record])
            rows = store.list_proposals()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["status"], "Approved")
            self.assertEqual(rows[0]["decision_at"], "2026-09-24T20:00:00-05:00")

    def test_private_values_are_not_committed_to_public_command_center_state(self):
        state = json.loads((ROOT / "site" / "command-center" / "state.json").read_text(encoding="utf-8"))
        text = json.dumps(state).lower()
        self.assertNotIn('"usage_history_records"', text)
        self.assertNotIn('"private_usage_records"', text)
        self.assertNotIn('"proposal_records_private"', text)
        self.assertFalse(state["privacy"]["public_reader_exposure"])
        private = state["legacy_import_source"]
        self.assertEqual(private["transport"], "authenticated-private-runtime")
        self.assertFalse(private["values_committed_to_repository"])
        self.assertNotIn("records", private["usage_history"])
        self.assertNotIn("records", private["book_change_proposals"])


if __name__ == "__main__":
    unittest.main()
