from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CC = ROOT / "site" / "command-center"


class CommandCenterTests(unittest.TestCase):
    def setUp(self):
        self.html = (CC / "index.html").read_text(encoding="utf-8")
        self.css = (CC / "cc.css").read_text(encoding="utf-8")
        self.js = (CC / "cc.js").read_text(encoding="utf-8")
        self.state = json.loads((CC / "state.json").read_text(encoding="utf-8"))

    def test_full_required_sections_exist(self):
        for section in ["today","pipeline","content","reader","controls","readiness","parity","operations"]:
            self.assertIn(f'id="{section}"', self.html)
        for heading in [
            "Publication pipeline","Six-story allocation","Images","Videos & podcasts","Watchlist",
            "Book bridges","Reader and Site","Manual controls","Production readiness","Schedule readiness",
            "Command Center data parity","Legacy operational history","Public review & application data",
            "Run history & timing","Source health","Incidents & recovery","Usage & cost","Reader engagement",
        ]:
            self.assertIn(heading, self.html)

    def test_public_access_and_public_reader_isolation_contract(self):
        self.assertIn('noindex,nofollow,noarchive', self.html)
        self.assertEqual(self.state["privacy"]["surface"], "public-command-center")
        self.assertFalse(self.state["privacy"]["public_reader_exposure"])
        self.assertFalse(self.state["command_center_site"]["public_pages_deployment_allowed"])
        for forbidden in ["site_project_id", "site_version_id", "deployment_id", "PRIVATE-DO-NOT-COPY"]:
            self.assertNotIn(forbidden, json.dumps(self.state))
        self.assertNotIn("password", self.js.lower())
        self.assertNotIn("authorization: bearer", self.js.lower())

    def test_canonical_controls_only(self):
        controls = {x["id"]: x for x in self.state["manual_controls"]}
        canonical = "actions/workflows/manual-daily-brief.yml"
        for control_id in ["build-entire-brief","resume-current-edition","force-replace"]:
            self.assertIn(canonical, controls[control_id]["url"])
        self.assertIn("reader-parity.yml", controls["validate-reader"]["url"])
        self.assertIn("force replacement off", controls["resume-current-edition"]["notes"])
        self.assertIn("2026-09-24", controls["force-replace"]["notes"])

    def test_schedule_creation_is_structurally_blocked(self):
        schedules = self.state["schedules"]
        self.assertFalse(schedules["creation_permitted"])
        self.assertFalse(schedules["old_system_decommissioned"])
        self.assertIn("Not permitted", schedules["blocker"])
        self.assertEqual([x["time"] for x in schedules["planned"]], ["07:00", "09:00"])
        self.assertTrue(all(x["created"] is False and x["enabled"] is False for x in schedules["planned"]))
        self.assertNotIn("schedule:", self.js.lower())
        self.assertNotIn("cron", self.js.lower())

    def test_story_and_image_contracts(self):
        stories = self.state["stories"]
        self.assertEqual(stories["count"], 6)
        self.assertTrue(stories["allocation_pass"])
        self.assertEqual(stories["allocation"], {
            "technical_ai_engineering": 2,
            "applied_genai_knowledge_workers": 2,
            "agents_non_technical_people": 2,
        })
        self.assertEqual(stories["agent_skills_count"], 1)
        self.assertEqual(self.state["images"]["accepted_count"], 6)
        self.assertTrue(all(x["dimensions"] == [1200, 630] for x in self.state["images"]["items"]))

    def test_unknown_usage_and_engagement_are_not_estimated(self):
        self.assertIsNone(self.state["usage_cost"]["work_usage"])
        self.assertIsNone(self.state["usage_cost"]["credit_usage"])
        self.assertFalse(self.state["usage_cost"]["estimated"])
        self.assertIsNone(self.state["engagement"]["ratings"]["count"])
        self.assertIsNone(self.state["engagement"]["private_comments"]["count"])

    def test_mobile_and_accessibility_basics(self):
        self.assertIn('name="viewport"', self.html)
        self.assertIn('class="skip-link"', self.html)
        self.assertIn('aria-label="Command Center sections"', self.html)
        self.assertIn('@media(max-width:720px)', self.css)
        self.assertIn('@media(max-width:420px)', self.css)
        self.assertIn('@media(prefers-reduced-motion:reduce)', self.css)

    def test_live_refresh_has_safe_committed_fallback(self):
        self.assertIn('state.json', self.js)
        self.assertIn('/branches/main', (CC / 'worker.mjs').read_text())
        self.assertIn('manual-daily-brief.yml/runs', (CC / 'worker.mjs').read_text())
        self.assertIn('command-center-data-parity-validation.yml/runs', (CC / 'worker.mjs').read_text())
        self.assertIn('saved snapshot retained', self.js)
        self.assertIn('Refresh failed', self.js)

    def test_data_parity_contract_is_public_safe_and_complete(self):
        parity = self.state["data_parity"]
        self.assertEqual(parity["required_domain_count"], 10)
        self.assertEqual(parity["unresolved_required_families"], 0)
        self.assertEqual(parity["privacy_leakage_defects"], 0)
        self.assertEqual(parity["full_system_validation"], "NOT REQUESTED")
        self.assertFalse(self.state["historical_data"]["private_values_included"])
        self.assertFalse(self.state["legacy_import_source"]["values_committed_to_repository"])
        self.assertEqual(len(self.state["data_domains"]), 10)


    def test_snapshot_builder_sanitizes_private_identifiers(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "state.json"
            subprocess.run([
                sys.executable, str(ROOT / "scripts" / "build_command_center_snapshot.py"),
                "--repo-root", str(ROOT), "--main-sha", self.state["source"]["main_sha"], "--output", str(out)
            ], check=True, capture_output=True, text=True)
            generated = json.loads(out.read_text(encoding="utf-8"))
            self.assertFalse(generated["schedules"]["creation_permitted"])
            self.assertTrue(all(not x["created"] and not x["enabled"] for x in generated["schedules"]["planned"]))
            text = json.dumps(generated)
            for forbidden in ["site_project_id", "site_version_id", "deployment_id"]:
                self.assertNotIn(forbidden, text)


if __name__ == "__main__":
    unittest.main()
