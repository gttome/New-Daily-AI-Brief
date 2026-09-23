from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

class Iteration32AccessTests(unittest.TestCase):
    def test_required_reader_surfaces_exist(self):
        for name in ["index.html","archive.html","watchlist.html","media.html","article.html","styles.css","app.js"]:
            self.assertTrue((SITE / name).is_file(), name)
        self.assertTrue((SITE / "command-center" / "index.html").is_file())
        self.assertTrue((SITE / "command-center" / "cc.js").is_file())

    def test_reader_is_clearly_shadow_and_has_required_interactions(self):
        home=(SITE/"index.html").read_text()
        app=(SITE/"app.js").read_text()
        self.assertIn("GREENFIELD TEST", home)
        self.assertIn("PRE-CUTOVER", home)
        self.assertIn("localStorage", app)
        self.assertIn("navigator.share", app)
        self.assertIn("navigator.clipboard", app)
        self.assertEqual(app.count('category:"Technical AI Engineering"'),2)
        self.assertEqual(app.count('category:"AI for Knowledge Workers"'),2)
        self.assertEqual(app.count('category:"Agents for Non-Technical Users"'),2)

    def test_phone_layout_and_viewport_are_present(self):
        css=(SITE/"styles.css").read_text()
        for name in ["index.html","archive.html","watchlist.html","media.html","article.html","command-center/index.html"]:
            self.assertIn('name="viewport"', (SITE/name).read_text())
        self.assertRegex(css, r"@media\(max-width:720px\)")

    def test_command_center_is_encrypted_and_contains_no_plain_payload(self):
        cc=(SITE/"command-center"/"cc.js").read_text()
        self.assertIn('crypto.subtle.decrypt', cc)
        self.assertIn('AES-GCM', cc)
        self.assertNotIn('shadow-2026-09-23-owner-test', cc)
        self.assertNotIn('ready_for_owner_testing', cc)
        self.assertNotIn('71a12a1278c1a509e6d3ef8784278097231e2083', cc)

    def test_deployment_is_pages_only_and_has_live_smoke(self):
        wf=(ROOT/".github/workflows/deploy-iteration32-test.yml").read_text()
        self.assertIn("actions/deploy-pages@v4", wf)
        self.assertIn("Greenfield Contracts", wf)
        self.assertIn("workflow_run", wf)
        self.assertIn("live-smoke", wf)
        self.assertIn("Mobile Safari", wf)
        self.assertNotIn("Daily-AI-Brief", wf.replace("New-Daily-AI-Brief",""))

if __name__ == "__main__":
    unittest.main()
