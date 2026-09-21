from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.editorial import classify_agent_skills, normalize_url
from new_daily_ai_brief.engine import RunEngine, start_daily_brief


class Iteration2DiscoveryEditorialTest(unittest.TestCase):
    def run_editorial(self, edition_date="2026-09-22"):
        td = tempfile.TemporaryDirectory()
        run = start_daily_brief(edition_date, state_root=td.name, editorial_only=True)
        engine = RunEngine(td.name, edition_date, editorial_only=True)
        return td, run, engine

    def test_metadata_retry_and_category_local_fallback(self):
        td, run, engine = self.run_editorial()
        self.addCleanup(td.cleanup)
        metrics = json.loads((engine.store.run_dir / "discovery-metrics.json").read_text())
        discovery = engine.store.load_artifact("discovery")["data"]
        self.assertEqual(metrics["metadata_failures"], 1)
        self.assertEqual(metrics["metadata_retries"], 1)
        self.assertEqual(discovery["fallback_tier_by_category"]["technical_ai_engineering"], 1)
        self.assertEqual(discovery["fallback_tier_by_category"]["agents_non_technical_people"], 0)
        self.assertEqual(discovery["fallback_tier_by_category"]["applied_genai_knowledge_workers"], 0)
        self.assertEqual(metrics["fallback_sources_used"], ["technical-fallback"])

    def test_freshness_and_normalized_url_novelty_reject_only_affected_candidates(self):
        td, run, engine = self.run_editorial()
        self.addCleanup(td.cleanup)
        discovery = engine.store.load_artifact("discovery")["data"]
        self.assertEqual(discovery["rejections"]["technical-stale-1"], "freshness")
        self.assertEqual(discovery["rejections"]["agent-prior-url-duplicate"], "novelty_url_collision")
        self.assertIn("applied-context-2", discovery["selected_candidate_ids"])
        self.assertEqual(
            normalize_url("HTTP://WWW.EXAMPLE.TEST/agents/prior-item/?utm_source=daily#section"),
            "https://example.test/agents/prior-item",
        )

    def test_semantic_agent_skills_classification(self):
        self.assertTrue(classify_agent_skills({
            "title": "Reusable agent workflow skill",
            "summary": "A repeatable procedure for an agent",
            "why_it_matters": "",
            "tags": [],
        }))
        self.assertFalse(classify_agent_skills({
            "title": "Agent approval workspace",
            "summary": "Human checkpoints for actions",
            "why_it_matters": "",
            "tags": ["agents"],
        }))

    def test_exact_2_2_2_and_exactly_one_agent_skills_story(self):
        td, run, engine = self.run_editorial()
        self.addCleanup(td.cleanup)
        edition = engine.store.load_artifact("edition")["data"]
        self.assertEqual(run["current_state"], "Building")
        self.assertEqual(run["completion_status"], "editorial_locked")
        self.assertEqual(len(edition["stories"]), 6)
        self.assertEqual(edition["allocation"], {"agents": 2, "applied": 2, "technical": 2})
        self.assertEqual(edition["agent_skills_count"], 1)
        self.assertIsNone(engine.store.load_artifact("publication-bundle"))

    def test_targeted_candidate_failure_resumes_without_chat_and_reuses_packets(self):
        with tempfile.TemporaryDirectory() as td:
            failing = RunEngine(
                td,
                "2026-09-22",
                failure_injection=FailureInjection(
                    "Acquiring", "synthetic_candidate_failure", "technical-evals-1"
                ),
                editorial_only=True,
            )
            with self.assertRaises(Exception):
                failing.run()
            failed = failing.store.load_run()
            self.assertEqual(failed["current_state"], "Recovering")
            packet_dir = failing.store.run_dir / "evidence-packets"
            before = {
                p.stem: json.loads(p.read_text())["content_digest"]
                for p in packet_dir.glob("*.json")
            }
            self.assertEqual(len(before), 5)
            state_before = json.loads((failing.store.run_dir / "discovery-state.json").read_text())
            scans_before = state_before["metrics"]["source_scans"]

            resumed = RunEngine(td, "2026-09-22", editorial_only=True)
            completed = resumed.run()
            after = {
                p.stem: json.loads(p.read_text())["content_digest"]
                for p in packet_dir.glob("*.json")
            }
            self.assertTrue(all(after[k] == v for k, v in before.items()))
            self.assertEqual(len(after), 6)
            state_after = json.loads((resumed.store.run_dir / "discovery-state.json").read_text())
            self.assertEqual(scans_before, state_after["metrics"]["source_scans"])
            self.assertEqual(completed["current_state"], "Building")
            self.assertEqual(completed["anti_rework"]["locked_stage_reexecutions"], 0)
            self.assertEqual(completed["anti_rework"]["full_pipeline_restarts"], 0)
            incident = resumed.store.load_incident()
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["candidate_id"], "technical-evals-1")

    def test_deterministic_replay_same_evidence_same_edition_digest(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            ea = RunEngine(a, "2026-09-22", editorial_only=True)
            eb = RunEngine(b, "2026-09-22", editorial_only=True)
            ea.run()
            eb.run()
            self.assertEqual(
                ea.store.load_artifact("discovery")["content_digest"],
                eb.store.load_artifact("discovery")["content_digest"],
            )
            self.assertEqual(
                ea.store.load_artifact("edition")["content_digest"],
                eb.store.load_artifact("edition")["content_digest"],
            )

    def test_three_consecutive_synthetic_exit_gate_runs_without_publication(self):
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                run = start_daily_brief(edition_date, state_root=td, editorial_only=True)
                engine = RunEngine(td, edition_date, editorial_only=True)
                edition = engine.store.load_artifact("edition")["data"]
                self.assertEqual(run["current_state"], "Building")
                self.assertFalse(run["manual_intervention"])
                self.assertEqual(len(edition["stories"]), 6)
                self.assertEqual(edition["agent_skills_count"], 1)
                self.assertIsNone(engine.store.load_artifact("media"))
                self.assertIsNone(engine.store.load_artifact("images"))
                self.assertIsNone(engine.store.load_artifact("watchlist"))
                self.assertIsNone(engine.store.load_artifact("publication-bundle"))

    def test_production_discovery_fails_closed_in_iteration2(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(Exception, "production discovery is intentionally unconfigured"):
                start_daily_brief(
                    "2026-09-22", mode="production", state_root=td, editorial_only=True
                )

    def test_schema_contracts_for_iteration2_exist(self):
        schema_dir = Path(__file__).resolve().parents[1] / "schemas"
        for name in ("source-registry", "novelty-index", "discovery", "evidence-packet"):
            doc = json.loads((schema_dir / f"{name}.schema.json").read_text())
            self.assertEqual(doc["$schema"], "https://json-schema.org/draft/2020-12/schema")


if __name__ == "__main__":
    unittest.main()
