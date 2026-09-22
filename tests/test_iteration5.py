from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.render import ReaderRenderError, ReaderSurfaceRenderer, RenderBoundaryFailure
from new_daily_ai_brief.store import CanonicalStore


class Iteration5ReaderRenderingTest(unittest.TestCase):
    DATE = "2026-09-22"

    def lock_iteration4(self, root: str, edition_date: str = DATE):
        run = start_daily_brief(edition_date, state_root=root, validation_only=True)
        self.assertEqual(run["current_state"], "Validating")
        self.assertEqual(run["completion_status"], "validation_locked")
        engine = RunEngine(root, edition_date, validation_only=True)
        self.assertEqual(
            engine.store.load_artifact("publication-bundle")["data"]["validation_result"],
            "passed",
        )
        return run, engine

    def render_iteration5(self, root: str, edition_date: str = DATE):
        baseline, baseline_engine = self.lock_iteration4(root, edition_date)
        before = dict(baseline["stage_executions"])
        run = start_daily_brief(edition_date, state_root=root, render_only=True)
        engine = RunEngine(root, edition_date, render_only=True)
        return before, run, engine, baseline_engine

    def upstream_digests(self, engine: RunEngine):
        return {
            name: engine.store.load_artifact(name)["content_digest"]
            for name in (
                "discovery",
                "edition",
                "rating-contract",
                "media",
                "watchlist",
                "book-bridges",
                "images",
                "publication-bundle",
            )
        }

    def assert_upstream_counts_unchanged(self, before, after):
        for stage, count in before.items():
            self.assertEqual(after["stage_executions"].get(stage), count, stage)

    def test_reader_surfaces_preserve_exact_locked_semantics_and_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            before, run, engine, _ = self.render_iteration5(td)
            reader = engine.store.load_artifact("reader-render")["data"]
            manifest = engine.store.load_artifact("route-manifest")["data"]
            edition = engine.store.load_artifact("edition")["data"]
            media = engine.store.load_artifact("media")["data"]
            watch = engine.store.load_artifact("watchlist")["data"]
            bridges = engine.store.load_artifact("book-bridges")["data"]
            images = engine.store.load_artifact("images")["data"]

            story_ids = [x["story_id"] for x in edition["stories"]]
            self.assertEqual(run["current_state"], "Validating")
            self.assertEqual(run["completion_status"], "render_locked")
            self.assertEqual(reader["story_order"], story_ids)
            self.assertEqual(reader["media"]["video_ids"], [x["media_id"] for x in media["videos"]])
            self.assertEqual(reader["media"]["podcast_ids"], [x["media_id"] for x in media["podcasts"]])
            self.assertEqual(reader["watchlist_counts"], watch["counts"])
            self.assertEqual(reader["bridge_decisions"], bridges["decisions"])
            self.assertEqual(
                reader["image_bindings"],
                [
                    {
                        "story_id": x["story_id"],
                        "image_id": x["image_id"],
                        "binary_digest": x["binary_digest"],
                    }
                    for x in images["images"]
                ],
            )
            self.assertEqual(reader["rating_contract"]["contract_version"], "five-star-v1")
            self.assertIsNone(reader["rating_contract"]["stored_rating_values"])
            self.assertFalse(reader["rating_contract"]["fabricated_rating_values"])
            self.assertEqual(reader["archive_membership"], [self.DATE])
            self.assertEqual(reader["feed_membership"], [self.DATE])
            self.assertFalse(reader["release_authorized"])

            expected_route_ids = [
                "current",
                "latest",
                "dated",
                *[f"story:{story_id}" for story_id in story_ids],
                "archive",
                "feed",
            ]
            self.assertEqual([x["route_id"] for x in reader["routes"]], expected_route_ids)
            self.assertEqual(len(reader["routes"]), 11)
            for route in reader["routes"]:
                self.assertTrue(all(route["structural_checks"].values()))
            for route in reader["routes"][:3]:
                self.assertEqual(route["semantic"]["story_ids"], story_ids)
                self.assertEqual(route["semantic"]["rating_contract"], "five-star-v1")
                self.assertIsNone(route["semantic"]["stored_rating_values"])
            story_routes = [x for x in reader["routes"] if x["kind"] == "story"]
            self.assertEqual([x["semantic"]["story_id"] for x in story_routes], story_ids)
            self.assertTrue(
                all(x["semantic"]["edition_story_order"] == story_ids for x in story_routes)
            )
            self.assertTrue(
                all('data-rating-contract="five-star-v1"' in x["content"] for x in reader["routes"] if x["content_type"] == "text/html" and x["kind"] in {"edition", "story"})
            )

            self.assertEqual(manifest["publication_bundle_digest"], engine.store.load_artifact("publication-bundle")["content_digest"])
            self.assertEqual(manifest["reader_render_digest"], engine.store.load_artifact("reader-render")["content_digest"])
            self.assertEqual(manifest["validation_result"], "passed")
            self.assertEqual(manifest["accessibility_structural_result"], "passed")
            self.assertTrue(all(manifest["validation_checks"].values()))
            self.assertFalse(manifest["release_authorized"])
            self.assertEqual([x["route_id"] for x in manifest["routes"]], expected_route_ids)

            self.assert_upstream_counts_unchanged(before, run)
            self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
            self.assertNotIn("releasing", run["stage_executions"])
            self.assertNotIn("deployed", run["stage_executions"])
            self.assertNotIn("release", run["stage_receipts"])
            self.assertIsNone(engine.store.load_artifact("completion"))

            metrics = json.loads((engine.store.run_dir / "iteration5-metrics.json").read_text())
            self.assertEqual(metrics["rendering"]["route_attempts"], 11)
            self.assertEqual(metrics["rendering"]["route_completions"], 11)
            self.assertEqual(metrics["rendering"]["archive_feed_attempts"], 2)
            self.assertGreaterEqual(metrics["manifest"]["validation_checks"], 20)

    def test_deterministic_reader_and_manifest_replay(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            self.render_iteration5(a)
            self.render_iteration5(b)
            ea = RunEngine(a, self.DATE, render_only=True)
            eb = RunEngine(b, self.DATE, render_only=True)
            self.assertEqual(
                ea.store.load_artifact("reader-render")["content_digest"],
                eb.store.load_artifact("reader-render")["content_digest"],
            )
            self.assertEqual(
                ea.store.load_artifact("route-manifest")["content_digest"],
                eb.store.load_artifact("route-manifest")["content_digest"],
            )

    def test_targeted_story_route_failure_recovers_without_locked_stage_reexecution(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration4(td)
            before = dict(baseline["stage_executions"])
            digests = self.upstream_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Validating",
                    "synthetic_story_route_failure",
                    "render:story:applied-workflow-1",
                ),
                render_only=True,
            )
            with self.assertRaises(RenderBoundaryFailure):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            state = json.loads((failing.store.run_dir / "reader-render-state.json").read_text())
            self.assertNotIn("story:applied-workflow-1", state["outputs"])
            completed_before = set(state["outputs"])
            self.assertGreaterEqual(len(completed_before), 5)

            resumed = RunEngine(td, self.DATE, render_only=True)
            complete = resumed.run()
            self.assertEqual(complete["completion_status"], "render_locked")
            self.assertEqual(self.upstream_digests(resumed), digests)
            self.assert_upstream_counts_unchanged(before, complete)
            final_state = json.loads((resumed.store.run_dir / "reader-render-state.json").read_text())
            self.assertTrue(completed_before.issubset(set(final_state["outputs"])))
            self.assertGreaterEqual(final_state["metrics"]["route_cache_reuse"], len(completed_before))
            self.assertEqual(complete["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(complete["anti_rework"]["full_pipeline_restarts"], 0)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "route")
            self.assertEqual(
                incident["recovery_receipt"]["boundary_id"],
                "story:applied-workflow-1",
            )

    def test_targeted_archive_failure_recovers_with_prior_routes_reused(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration4(td)
            before = dict(baseline["stage_executions"])
            digests = self.upstream_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Validating", "synthetic_archive_render_failure", "render:archive"
                ),
                render_only=True,
            )
            with self.assertRaises(RenderBoundaryFailure):
                failing.run()
            state = json.loads((failing.store.run_dir / "reader-render-state.json").read_text())
            self.assertNotIn("archive", state["outputs"])
            self.assertEqual(len(state["outputs"]), 9)

            resumed = RunEngine(td, self.DATE, render_only=True)
            complete = resumed.run()
            self.assertEqual(self.upstream_digests(resumed), digests)
            self.assert_upstream_counts_unchanged(before, complete)
            final_state = json.loads((resumed.store.run_dir / "reader-render-state.json").read_text())
            self.assertGreaterEqual(final_state["metrics"]["route_cache_reuse"], 9)
            self.assertIn("archive", final_state["outputs"])
            self.assertIn("feed", final_state["outputs"])
            incident = resumed.store.load_incident()
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "archive_feed")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "archive")

    def test_manifest_validation_failure_recovers_with_reader_render_locked_and_reused(self):
        with tempfile.TemporaryDirectory() as td:
            baseline, engine = self.lock_iteration4(td)
            before = dict(baseline["stage_executions"])
            digests = self.upstream_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Validating",
                    "synthetic_manifest_validation_failure",
                    "render:manifest-validation",
                ),
                render_only=True,
            )
            with self.assertRaises(RenderBoundaryFailure):
                failing.run()
            reader_digest = failing.store.load_artifact("reader-render")["content_digest"]
            self.assertIsNone(failing.store.load_artifact("route-manifest"))
            self.assertEqual(failing.store.load_run()["current_state"], "Recovering")

            resumed = RunEngine(td, self.DATE, render_only=True)
            complete = resumed.run()
            self.assertEqual(
                resumed.store.load_artifact("reader-render")["content_digest"],
                reader_digest,
            )
            self.assertEqual(
                resumed.store.load_artifact("route-manifest")["data"]["validation_result"],
                "passed",
            )
            self.assertEqual(self.upstream_digests(resumed), digests)
            self.assert_upstream_counts_unchanged(before, complete)
            self.assertEqual(complete["stage_executions"]["validating:reader-render"], 1)
            self.assertEqual(complete["stage_executions"]["validating:route-manifest"], 2)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["recovery_receipt"]["boundary_type"], "manifest_validation")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "manifest-validation")

    def test_fail_closed_on_corrupted_locked_publication_bundle(self):
        with tempfile.TemporaryDirectory() as td:
            self.lock_iteration4(td)
            engine = RunEngine(td, self.DATE, render_only=True)
            bundle = engine.store.load_artifact("publication-bundle")
            bundle["data"]["validation_result"] = "failed"
            engine.store._atomic_write(engine.store.artifact_path("publication-bundle"), bundle)

            with self.assertRaises(RenderBoundaryFailure):
                engine.run()
            self.assertEqual(engine.store.load_run()["current_state"], "Recovering")
            self.assertIsNone(engine.store.load_artifact("reader-render"))
            self.assertIsNone(engine.store.load_artifact("route-manifest"))

    def test_fail_closed_on_corrupted_cached_reader_route_before_reuse(self):
        with tempfile.TemporaryDirectory() as td:
            self.render_iteration5(td)
            engine = RunEngine(td, self.DATE, render_only=True)
            reader = engine.store.load_artifact("reader-render")
            reader["data"]["routes"][0]["content"] += "<!-- corruption -->"
            engine.store._atomic_write(engine.store.artifact_path("reader-render"), reader)

            with self.assertRaises(RenderBoundaryFailure):
                engine.run()
            self.assertEqual(engine.store.load_run()["current_state"], "Recovering")

    def test_production_render_adapter_is_fail_closed_without_approved_dependency(self):
        with tempfile.TemporaryDirectory() as td:
            store = CanonicalStore(Path(td), self.DATE, "production")
            renderer = ReaderSurfaceRenderer(store, self.DATE, "production", None)
            with self.assertRaisesRegex(ReaderRenderError, "fail-closed"):
                renderer.build_reader_render()

    def test_three_consecutive_render_only_exit_gate_runs(self):
        digests = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as replay_td:
                baseline, _ = self.lock_iteration4(td, edition_date)
                before = dict(baseline["stage_executions"])
                run = start_daily_brief(edition_date, state_root=td, render_only=True)
                engine = RunEngine(td, edition_date, render_only=True)

                replay_baseline, _ = self.lock_iteration4(replay_td, edition_date)
                replay_before = dict(replay_baseline["stage_executions"])
                replay = start_daily_brief(edition_date, state_root=replay_td, render_only=True)
                replay_engine = RunEngine(replay_td, edition_date, render_only=True)

                self.assertEqual(run["current_state"], "Validating")
                self.assertEqual(run["completion_status"], "render_locked")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(len(engine.store.load_artifact("reader-render")["data"]["routes"]), 11)
                self.assertEqual(
                    engine.store.load_artifact("route-manifest")["data"]["validation_result"],
                    "passed",
                )
                self.assertEqual(
                    engine.store.load_artifact("reader-render")["content_digest"],
                    replay_engine.store.load_artifact("reader-render")["content_digest"],
                )
                self.assertEqual(
                    engine.store.load_artifact("route-manifest")["content_digest"],
                    replay_engine.store.load_artifact("route-manifest")["content_digest"],
                )
                self.assert_upstream_counts_unchanged(before, run)
                self.assert_upstream_counts_unchanged(replay_before, replay)
                self.assertEqual(run["anti_rework"]["locked_stage_reexecutions"], 0)
                self.assertEqual(run["anti_rework"]["full_pipeline_restarts"], 0)
                self.assertNotIn("releasing", run["stage_executions"])
                self.assertNotIn("deployed", run["stage_executions"])
                self.assertNotIn("release", run["stage_receipts"])
                self.assertIsNone(engine.store.load_artifact("completion"))
                digests.append(
                    (
                        edition_date,
                        engine.store.load_artifact("reader-render")["content_digest"],
                        engine.store.load_artifact("route-manifest")["content_digest"],
                    )
                )
        self.assertEqual(len(digests), 3)

    def test_publication_bundle_invalidation_only_invalidates_render_descendants(self):
        with tempfile.TemporaryDirectory() as td:
            self.render_iteration5(td)
            engine = RunEngine(td, self.DATE, render_only=True)
            upstream = {
                name: engine.store.load_artifact(name)["status"]
                for name in (
                    "discovery",
                    "edition",
                    "rating-contract",
                    "media",
                    "watchlist",
                    "book-bridges",
                    "images",
                )
            }
            changed = engine.store.invalidate("publication-bundle", "synthetic_dependency_change")
            self.assertIn("publication-bundle", changed)
            self.assertIn("reader-render", changed)
            self.assertIn("route-manifest", changed)
            for name, status in upstream.items():
                self.assertEqual(status, "locked")
                self.assertEqual(engine.store.load_artifact(name)["status"], "locked")

    def test_iteration5_contract_schemas_exist_and_are_versioned(self):
        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        for name in ("reader-render", "route-render-manifest"):
            doc = json.loads((schema_dir / f"{name}.schema.json").read_text())
            self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
