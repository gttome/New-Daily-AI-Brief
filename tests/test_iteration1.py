from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import (
    IllegalTransition,
    IncompleteCompletion,
    RunEngine,
    SyntheticFailure,
    projection_freshness,
    scheduled_start,
    start_daily_brief,
)
from new_daily_ai_brief.store import CanonicalStore, LeaseCollision, LockedArtifactMutation


class Iteration1ContractsTest(unittest.TestCase):
    DATE = "2026-09-22"

    def temp_root(self):
        return tempfile.TemporaryDirectory()

    def test_duplicate_run_start_is_idempotent(self):
        with self.temp_root() as td:
            first = start_daily_brief(self.DATE, state_root=td)
            second = start_daily_brief(self.DATE, state_root=td)
            self.assertEqual(first["run_id"], second["run_id"])
            self.assertEqual(second["current_state"], "Complete")
            self.assertEqual(first["stage_executions"], second["stage_executions"])

    def test_lease_collision_allows_one_owner_only(self):
        with self.temp_root() as td:
            store = CanonicalStore(Path(td), self.DATE, "synthetic")
            store.acquire_lease("dab-2026-09-22-synthetic", "owner-a")
            with self.assertRaises(LeaseCollision):
                store.acquire_lease("dab-2026-09-22-synthetic", "owner-b")

    def test_legal_and_illegal_transition(self):
        with self.temp_root() as td:
            engine = RunEngine(td, self.DATE)
            run = engine.load_or_create()
            engine.transition(run, "Acquiring")
            self.assertEqual(run["current_state"], "Acquiring")
            with self.assertRaises(IllegalTransition):
                engine.transition(run, "Complete")

    def test_locked_artifact_mutation_is_rejected(self):
        with self.temp_root() as td:
            store = CanonicalStore(Path(td), self.DATE, "synthetic")
            store.lock_artifact("edition", "e1", {"value": 1}, "acquiring", [])
            with self.assertRaises(LockedArtifactMutation):
                store.lock_artifact("edition", "e1", {"value": 2}, "acquiring", [])

    def test_dependency_invalidation_only_invalidates_descendants(self):
        with self.temp_root() as td:
            start_daily_brief(self.DATE, state_root=td)
            store = CanonicalStore(Path(td), self.DATE, "synthetic")
            invalidated = set(store.invalidate("media", "synthetic dependency change"))
            self.assertIn("media", invalidated)
            self.assertIn("publication-bundle", invalidated)
            self.assertIn("book-change-evaluation", invalidated)
            self.assertIn("projection-watermark", invalidated)
            self.assertIn("completion", invalidated)
            self.assertNotIn("edition", invalidated)
            self.assertNotIn("images", invalidated)
            self.assertNotIn("watchlist", invalidated)
            self.assertEqual(store.load_artifact("edition")["status"], "locked")
            self.assertEqual(store.load_artifact("images")["status"], "locked")

    def test_injected_failure_resume_without_chat_preserves_locks(self):
        with self.temp_root() as td:
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection("Validating"),
            )
            with self.assertRaises(SyntheticFailure):
                failing.run()
            failed_run = failing.store.load_run()
            self.assertEqual(failed_run["current_state"], "Recovering")
            before = {
                name: failing.store.load_artifact(name)["content_digest"]
                for name in ("edition", "rating-contract", "media", "images", "watchlist")
            }

            resumed = RunEngine(td, self.DATE)
            completed = resumed.run()
            after = {
                name: resumed.store.load_artifact(name)["content_digest"]
                for name in before
            }
            self.assertEqual(before, after)
            self.assertEqual(completed["current_state"], "Complete")
            self.assertEqual(completed["completion_status"], "complete")
            self.assertEqual(completed["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(completed["anti_rework"]["full_pipeline_restarts"], 0)
            self.assertEqual(completed["stage_executions"]["acquiring"], 1)
            self.assertEqual(completed["stage_executions"]["building:media"], 1)
            self.assertEqual(completed["stage_executions"]["building:images"], 1)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["result"], "recovered")
            self.assertEqual(
                set(incident["recovery_receipt"]["retained_locks"]),
                {"discovery", "edition", "rating-contract", "media", "images", "watchlist", "book-bridges"},
            )

    def test_schema_migration_from_0_9_run(self):
        with self.temp_root() as td:
            store = CanonicalStore(Path(td), self.DATE, "synthetic")
            old = {
                "schema_version": "0.9.0",
                "run_id": "old-run",
                "edition_date": self.DATE,
                "mode": "synthetic",
                "current_state": "Ready",
                "completion_status": "in_progress",
            }
            store._atomic_write(store.run_path, old)
            migrated = store.load_run()
            self.assertEqual(migrated["schema_version"], "1.0.0")
            self.assertIn("anti_rework", migrated)
            self.assertIn("stage_receipts", migrated)

    def test_completion_rejects_missing_book_change_evaluation(self):
        with self.temp_root() as td:
            engine = RunEngine(td, self.DATE)
            run = engine.run()
            engine.store.artifact_path("book-change-evaluation").unlink()
            with self.assertRaises(IncompleteCompletion):
                engine._completion(run)

    def test_projection_watermark_binds_final_production_identity(self):
        with self.temp_root() as td:
            engine = RunEngine(td, self.DATE)
            engine.run()
            watermark = engine.store.load_artifact("projection-watermark")["data"]
            completion = engine.store.load_artifact("completion")["data"]
            self.assertEqual(
                watermark["final_production_identity"],
                completion["final_production_identity"],
            )
            self.assertEqual(watermark["edition_date"], self.DATE)
            self.assertEqual(watermark["run_id"], engine.run_id)

    def test_projection_watermark_mismatch_is_degraded(self):
        with self.temp_root() as td:
            engine = RunEngine(td, self.DATE)
            engine.run()
            watermark = engine.store.load_artifact("projection-watermark")
            self.assertEqual(projection_freshness(watermark, "wrong-production-id")["status"], "degraded")
            expected = watermark["data"]["final_production_identity"]
            self.assertEqual(projection_freshness(watermark, expected)["status"], "current")

    def test_manual_entry_point_starts_synthetic_run(self):
        with self.temp_root() as td:
            run = start_daily_brief(self.DATE, mode="synthetic", state_root=td)
            self.assertEqual(run["current_state"], "Complete")
            self.assertEqual(run["mode"], "synthetic")

    def test_scheduled_adapter_calls_same_entry_point(self):
        expected = {"current_state": "Complete"}
        with patch("new_daily_ai_brief.engine.start_daily_brief", return_value=expected) as entry:
            result = scheduled_start(self.DATE, mode="production", state_root="x", owner="scheduler")
        self.assertEqual(result, expected)
        entry.assert_called_once_with(self.DATE, "production", "x", "scheduler")

    def test_deterministic_replay_same_locked_inputs_same_bundle_digest(self):
        with self.temp_root() as td1, self.temp_root() as td2:
            a = RunEngine(td1, self.DATE)
            b = RunEngine(td2, self.DATE)
            a.run()
            b.run()
            self.assertEqual(
                a.store.load_artifact("publication-bundle")["content_digest"],
                b.store.load_artifact("publication-bundle")["content_digest"],
            )

    def test_required_contract_files_exist_and_are_versioned(self):
        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        required = {
            "run", "edition", "media", "images", "watchlist", "publication-bundle",
            "completion", "incident", "book-change-evaluation", "rating-contract",
            "projection-watermark", "lease",
        }
        found = {p.name.removesuffix(".schema.json") for p in schema_dir.glob("*.schema.json")}
        self.assertTrue(required.issubset(found))
        for name in required:
            doc = json.loads((schema_dir / f"{name}.schema.json").read_text())
            self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_five_star_contract_and_legacy_version_rule(self):
        with self.temp_root() as td:
            engine = RunEngine(td, self.DATE)
            engine.run()
            rating = engine.store.load_artifact("rating-contract")["data"]
            self.assertEqual(rating["contract_version"], "five-star-v1")
            self.assertEqual(rating["scale"], {"min": 1, "max": 5, "step": 1})
            self.assertIn("no_silent_conversion", rating["legacy_policy"])


if __name__ == "__main__":
    unittest.main()
