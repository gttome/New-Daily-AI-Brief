from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.pre_release import PreReleaseError, PreReleasePipeline, ValidationBoundaryFailure
from new_daily_ai_brief.store import CanonicalStore


class Iteration4ValidationOnlyTest(unittest.TestCase):
    DATE = "2026-09-22"

    def lock_iteration3_then_validate(self, root: str, edition_date: str = DATE):
        baseline = start_daily_brief(edition_date, state_root=root, build_only=True)
        before = dict(baseline["stage_executions"])
        run = start_daily_brief(edition_date, state_root=root, validation_only=True)
        engine = RunEngine(root, edition_date, validation_only=True)
        return before, run, engine

    def test_exactly_six_story_specific_images_and_bounded_retry(self):
        with tempfile.TemporaryDirectory() as td:
            _, run, engine = self.lock_iteration3_then_validate(td)
            images = engine.store.load_artifact("images")["data"]
            self.assertEqual(run["current_state"], "Validating")
            self.assertEqual(run["completion_status"], "validation_locked")
            self.assertEqual(images["accepted_count"], 6)
            self.assertEqual(len(images["images"]), 6)
            self.assertEqual(len({x["story_id"] for x in images["images"]}), 6)
            self.assertEqual(len({x["composition_id"] for x in images["images"]}), 6)
            for image in images["images"]:
                self.assertTrue(image["accepted"])
                self.assertEqual((image["width"], image["height"]), (1200, 630))
                self.assertIn(image["format"], {"webp", "png"})
                self.assertTrue(image["quality"]["professional_textbook_editorial"])
                self.assertTrue(image["quality"]["mechanism_explanatory"])
                self.assertTrue(image["quality"]["white_background"])
            metrics = json.loads((engine.store.run_dir / "iteration4-metrics.json").read_text())
            self.assertEqual(metrics["images"]["image_attempts"], 7)
            self.assertEqual(metrics["images"]["retries"], 1)
            self.assertEqual(metrics["images"]["rejections"], 1)
            self.assertEqual(metrics["images"]["acceptances"], 6)

    def test_targeted_one_image_failure_recovers_without_upstream_reexecution(self):
        with tempfile.TemporaryDirectory() as td:
            baseline = start_daily_brief(self.DATE, state_root=td, build_only=True)
            upstream_counts = dict(baseline["stage_executions"])
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Building", "synthetic_one_image_failure", "image:applied-workflow-1"
                ),
                validation_only=True,
            )
            with self.assertRaises(Exception):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            image_state = json.loads((failing.store.run_dir / "image-state.json").read_text())
            self.assertEqual(
                set(image_state["accepted"]),
                {"agent-skill-1", "agent-general-1"},
            )
            upstream_digests = {
                name: failing.store.load_artifact(name)["content_digest"]
                for name in ("discovery", "edition", "media", "watchlist", "book-bridges", "rating-contract")
            }

            resumed = RunEngine(td, self.DATE, validation_only=True)
            complete = resumed.run()
            self.assertEqual(complete["current_state"], "Validating")
            self.assertEqual(complete["completion_status"], "validation_locked")
            for name, value in upstream_digests.items():
                self.assertEqual(resumed.store.load_artifact(name)["content_digest"], value)
            for stage in (
                "acquiring",
                "deciding",
                "building:media",
                "building:watchlist",
                "building:book-bridges",
            ):
                self.assertEqual(complete["stage_executions"][stage], upstream_counts[stage])
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)
            final_state = json.loads((resumed.store.run_dir / "image-state.json").read_text())
            self.assertGreaterEqual(final_state["metrics"]["accepted_image_reuse"], 2)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "image")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "applied-workflow-1")

    def test_validation_boundary_failure_recovers_with_locked_build_artifacts(self):
        with tempfile.TemporaryDirectory() as td:
            baseline = start_daily_brief(self.DATE, state_root=td, build_only=True)
            upstream_counts = dict(baseline["stage_executions"])
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection("Validating", "synthetic_validation_boundary_failure"),
                validation_only=True,
            )
            with self.assertRaises(Exception):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            images_digest = failing.store.load_artifact("images")["content_digest"]
            self.assertIsNone(failing.store.load_artifact("publication-bundle"))

            resumed = RunEngine(td, self.DATE, validation_only=True)
            complete = resumed.run()
            self.assertEqual(complete["current_state"], "Validating")
            self.assertEqual(resumed.store.load_artifact("images")["content_digest"], images_digest)
            self.assertEqual(resumed.store.load_artifact("publication-bundle")["data"]["validation_result"], "passed")
            for stage in ("acquiring", "deciding", "building:media", "building:watchlist", "building:book-bridges"):
                self.assertEqual(complete["stage_executions"][stage], upstream_counts[stage])
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)

    def test_fail_closed_validation_detects_corrupted_required_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            start_daily_brief(self.DATE, state_root=td, build_only=True)
            engine = RunEngine(td, self.DATE, validation_only=True)
            media = engine.store.load_artifact("media")
            media["data"]["podcasts"] = media["data"]["podcasts"][:1]
            engine.store._atomic_write(engine.store.artifact_path("media"), media)
            with self.assertRaises(ValidationBoundaryFailure):
                engine.run()
            failed = engine.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            self.assertIsNone(engine.store.load_artifact("publication-bundle"))

    def test_bundle_binds_all_required_locked_inputs_and_replays_deterministically(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.lock_iteration3_then_validate(a)
            self.lock_iteration3_then_validate(b)
            ea = RunEngine(a, self.DATE, validation_only=True)
            eb = RunEngine(b, self.DATE, validation_only=True)
            bundle_a = ea.store.load_artifact("publication-bundle")
            bundle_b = eb.store.load_artifact("publication-bundle")
            images_a = ea.store.load_artifact("images")
            images_b = eb.store.load_artifact("images")
            self.assertEqual(images_a["content_digest"], images_b["content_digest"])
            self.assertEqual(bundle_a["content_digest"], bundle_b["content_digest"])
            self.assertEqual(
                set(bundle_a["data"]["ordered_input_digests"]),
                {"edition", "media", "images", "watchlist", "book-bridges", "rating-contract"},
            )
            self.assertTrue(all(bundle_a["data"]["validation_checks"].values()))
            self.assertFalse(bundle_a["data"]["release_authorized"])

    def test_production_image_adapter_is_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            store = CanonicalStore(Path(td), self.DATE, "production")
            store.lock_artifact(
                "edition",
                "production-test-edition",
                {"stories": []},
                "deciding",
                [],
            )
            pipeline = PreReleasePipeline(store, self.DATE, "production", None)
            with self.assertRaises(PreReleaseError):
                pipeline.build_images()

    def test_three_consecutive_validation_only_exit_gate_runs_reuse_iteration3_locks(self):
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as replay_td:
                baseline = start_daily_brief(edition_date, state_root=td, build_only=True)
                before = dict(baseline["stage_executions"])
                run = start_daily_brief(edition_date, state_root=td, validation_only=True)
                engine = RunEngine(td, edition_date, validation_only=True)
                replay_baseline = start_daily_brief(edition_date, state_root=replay_td, build_only=True)
                replay_before = dict(replay_baseline["stage_executions"])
                replay = start_daily_brief(edition_date, state_root=replay_td, validation_only=True)
                replay_engine = RunEngine(replay_td, edition_date, validation_only=True)

                self.assertEqual(run["current_state"], "Validating")
                self.assertEqual(run["completion_status"], "validation_locked")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(engine.store.load_artifact("images")["data"]["accepted_count"], 6)
                self.assertEqual(engine.store.load_artifact("publication-bundle")["data"]["validation_result"], "passed")
                self.assertEqual(
                    engine.store.load_artifact("publication-bundle")["content_digest"],
                    replay_engine.store.load_artifact("publication-bundle")["content_digest"],
                )
                for stage in ("acquiring", "deciding", "building:media", "building:watchlist", "building:book-bridges"):
                    self.assertEqual(run["stage_executions"][stage], before[stage])
                    self.assertEqual(replay["stage_executions"][stage], replay_before[stage])
                self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
                self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
                self.assertNotIn("releasing", run["stage_executions"])
                self.assertNotIn("deployed", run["stage_executions"])
                self.assertNotIn("release", run["stage_receipts"])
                self.assertIsNone(engine.store.load_artifact("completion"))

    def test_iteration4_contract_schemas_exist_and_are_versioned(self):
        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        for name in ("images", "publication-bundle", "image-catalog"):
            doc = json.loads((schema_dir / f"{name}.schema.json").read_text())
            self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
