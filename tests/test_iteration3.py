from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief


class Iteration3BuildStageTest(unittest.TestCase):
    DATE = "2026-09-22"

    def run_build(self, edition_date: str = DATE):
        td = tempfile.TemporaryDirectory()
        run = start_daily_brief(edition_date, state_root=td.name, build_only=True)
        engine = RunEngine(td.name, edition_date, build_only=True)
        return td, run, engine

    def test_media_bounded_fallback_produces_exactly_two_verified_each(self):
        td, run, engine = self.run_build()
        self.addCleanup(td.cleanup)
        media = engine.store.load_artifact("media")["data"]
        self.assertEqual(run["current_state"], "Building")
        self.assertEqual(run["completion_status"], "build_locked")
        self.assertEqual(len(media["videos"]), 2)
        self.assertEqual(len(media["podcasts"]), 2)
        self.assertTrue(all(x["verified"] for x in media["videos"] + media["podcasts"]))
        self.assertEqual(media["verified_counts"], {"videos": 2, "podcasts": 2})
        self.assertEqual(media["decision_metrics"]["availability_failures"], 2)
        self.assertEqual(
            set(media["decision_metrics"]["fallback_sources_used"]),
            {"video-fallback", "podcast-fallback"},
        )

    def test_deterministic_media_replay(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            start_daily_brief(self.DATE, state_root=a, build_only=True)
            start_daily_brief(self.DATE, state_root=b, build_only=True)
            ea = RunEngine(a, self.DATE, build_only=True)
            eb = RunEngine(b, self.DATE, build_only=True)
            self.assertEqual(
                ea.store.load_artifact("media")["content_digest"],
                eb.store.load_artifact("media")["content_digest"],
            )

    def test_watchlist_classification_is_date_current(self):
        expectations = {
            "2026-09-22": {"new_today": 1, "updated_today": 1, "carried_forward": 1},
            "2026-09-23": {"new_today": 1, "updated_today": 0, "carried_forward": 3},
            "2026-09-24": {"new_today": 1, "updated_today": 0, "carried_forward": 4},
        }
        for edition_date, expected in expectations.items():
            with tempfile.TemporaryDirectory() as td:
                start_daily_brief(edition_date, state_root=td, build_only=True)
                engine = RunEngine(td, edition_date, build_only=True)
                watch = engine.store.load_artifact("watchlist")["data"]
                self.assertEqual(watch["edition_date"], edition_date)
                self.assertEqual(watch["counts"], expected)

    def test_targeted_watchlist_source_failure_recovers_without_editorial_reexecution(self):
        with tempfile.TemporaryDirectory() as td:
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Building", "synthetic_watchlist_source_failure", "watch-source-b"
                ),
                build_only=True,
            )
            with self.assertRaises(Exception):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            before = {
                name: failing.store.load_artifact(name)["content_digest"]
                for name in ("discovery", "edition", "media")
            }
            watch_state_before = json.loads(
                (failing.store.run_dir / "watchlist-state.json").read_text()
            )
            self.assertEqual(watch_state_before["checked_sources"], ["watch-source-a"])
            acquiring_before = failed["stage_executions"]["acquiring"]
            deciding_before = failed["stage_executions"]["deciding"]

            resumed = RunEngine(td, self.DATE, build_only=True)
            complete = resumed.run()
            after = {
                name: resumed.store.load_artifact(name)["content_digest"]
                for name in before
            }
            self.assertEqual(before, after)
            self.assertEqual(complete["current_state"], "Building")
            self.assertEqual(complete["completion_status"], "build_locked")
            self.assertEqual(complete["stage_executions"]["acquiring"], acquiring_before)
            self.assertEqual(complete["stage_executions"]["deciding"], deciding_before)
            self.assertEqual(complete["stage_executions"]["building:media"], 1)
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)
            watch_state_after = json.loads(
                (resumed.store.run_dir / "watchlist-state.json").read_text()
            )
            self.assertEqual(watch_state_after["metrics"]["source_checks"], 3)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "watchlist_source")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "watch-source-b")

    def test_media_boundary_failure_resumes_inside_building(self):
        with tempfile.TemporaryDirectory() as td:
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Building", "synthetic_media_failure", "video-fallback-1"
                ),
                build_only=True,
            )
            with self.assertRaises(Exception):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            edition_digest = failing.store.load_artifact("edition")["content_digest"]
            discovery_digest = failing.store.load_artifact("discovery")["content_digest"]

            resumed = RunEngine(td, self.DATE, build_only=True)
            complete = resumed.run()
            self.assertEqual(complete["current_state"], "Building")
            self.assertEqual(
                resumed.store.load_artifact("edition")["content_digest"], edition_digest
            )
            self.assertEqual(
                resumed.store.load_artifact("discovery")["content_digest"], discovery_digest
            )
            self.assertEqual(complete["stage_executions"]["acquiring"], 1)
            self.assertEqual(complete["stage_executions"]["deciding"], failed["stage_executions"]["deciding"])
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)

    def test_book_bridge_mapping_is_centralized_deterministic_and_allows_no_bridge(self):
        td, run, engine = self.run_build()
        self.addCleanup(td.cleanup)
        bridges = engine.store.load_artifact("book-bridges")["data"]
        self.assertEqual(len(bridges["decisions"]), 6)
        by_story = {x["story_id"]: x for x in bridges["decisions"]}
        self.assertEqual(by_story["agent-skill-1"]["decision"], "bridge")
        self.assertEqual(by_story["applied-context-2"]["decision"], "bridge")
        self.assertEqual(by_story["technical-grounding-1"]["decision"], "bridge")
        self.assertEqual(by_story["agent-general-1"]["decision"], "no_bridge")
        self.assertIsNone(by_story["agent-general-1"]["series_url"])
        self.assertTrue(all(x["evidence_digest"].startswith("sha256:") for x in bridges["decisions"]))

        with tempfile.TemporaryDirectory() as other:
            start_daily_brief(self.DATE, state_root=other, build_only=True)
            replay = RunEngine(other, self.DATE, build_only=True)
            self.assertEqual(
                engine.store.load_artifact("book-bridges")["content_digest"],
                replay.store.load_artifact("book-bridges")["content_digest"],
            )

    def test_same_locked_inputs_reproduce_all_build_artifact_digests(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            start_daily_brief(self.DATE, state_root=a, build_only=True)
            start_daily_brief(self.DATE, state_root=b, build_only=True)
            ea = RunEngine(a, self.DATE, build_only=True)
            eb = RunEngine(b, self.DATE, build_only=True)
            for name in ("media", "watchlist", "book-bridges"):
                self.assertEqual(
                    ea.store.load_artifact(name)["content_digest"],
                    eb.store.load_artifact(name)["content_digest"],
                )

    def test_build_only_has_no_images_rendering_deployment_or_publication(self):
        td, run, engine = self.run_build()
        self.addCleanup(td.cleanup)
        self.assertEqual(run["current_state"], "Building")
        self.assertIsNone(engine.store.load_artifact("images"))
        self.assertIsNone(engine.store.load_artifact("publication-bundle"))
        self.assertNotIn("releasing", run["stage_executions"])
        self.assertNotIn("deployed", run["stage_executions"])

    def test_three_consecutive_exit_gate_runs(self):
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                run = start_daily_brief(edition_date, state_root=td, build_only=True)
                engine = RunEngine(td, edition_date, build_only=True)
                media = engine.store.load_artifact("media")["data"]
                watch = engine.store.load_artifact("watchlist")["data"]
                bridges = engine.store.load_artifact("book-bridges")["data"]
                self.assertEqual(run["current_state"], "Building")
                self.assertEqual(run["completion_status"], "build_locked")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(len(media["videos"]), 2)
                self.assertEqual(len(media["podcasts"]), 2)
                self.assertTrue(all(x["verified"] for x in media["videos"] + media["podcasts"]))
                self.assertEqual(watch["edition_date"], edition_date)
                self.assertEqual(len(bridges["decisions"]), 6)
                self.assertEqual(run["stage_executions"]["acquiring"], 1)
                self.assertEqual(run["stage_executions"]["deciding"], 2)
                self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
                self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
                self.assertIsNone(engine.store.load_artifact("images"))
                self.assertIsNone(engine.store.load_artifact("publication-bundle"))

    def test_build_telemetry_records_required_metrics(self):
        td, run, engine = self.run_build()
        self.addCleanup(td.cleanup)
        metrics = json.loads((engine.store.run_dir / "build-metrics.json").read_text())
        self.assertGreaterEqual(metrics["media"]["source_scans"], 4)
        self.assertEqual(metrics["media"]["availability_failures"], 2)
        self.assertEqual(metrics["watchlist"]["source_checks"], 3)
        self.assertEqual(metrics["bridges"]["decisions"], 6)
        self.assertIn("fallback_sources_used", metrics["media"])
        self.assertIn("cache_reuse", metrics["media"])
        self.assertIn("elapsed_ms", metrics["media"])
        self.assertIn("elapsed_ms", metrics["watchlist"])
        self.assertIn("elapsed_ms", metrics["bridges"])

    def test_iteration3_contract_schemas_exist_and_are_versioned(self):
        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        for name in (
            "book-bridges",
            "media-registry",
            "watchlist-registry",
            "book-bridge-map",
        ):
            doc = json.loads((schema_dir / f"{name}.schema.json").read_text())
            self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
