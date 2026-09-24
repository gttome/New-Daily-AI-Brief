from pathlib import Path
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

    def test_command_center_is_full_private_source_and_safe(self):
        page=(SITE/"command-center"/"index.html").read_text()
        cc=(SITE/"command-center"/"cc.js").read_text()
        state=__import__("json").loads((SITE/"command-center"/"state.json").read_text())
        self.assertIn("PRIVATE OPERATIONS", page)
        self.assertIn("noindex,nofollow,noarchive", page)
        self.assertNotIn("crypto.subtle.decrypt", cc)
        self.assertNotIn("AES-GCM", cc)
        self.assertNotIn("location.hash", cc)
        self.assertIn("state.json", cc)
        self.assertEqual(state["privacy"]["surface"], "private-owner-only")
        self.assertFalse(state["privacy"]["public_reader_exposure"])
        self.assertFalse(state["command_center_site"]["public_pages_deployment_allowed"])
        self.assertFalse(state["schedules"]["creation_permitted"])
        self.assertTrue(all(not x["created"] and not x["enabled"] for x in state["schedules"]["planned"]))
        self.assertNotIn("password", cc.lower())
        self.assertNotIn("secret", cc.lower())

    def test_deployment_is_reader_preview_only_and_has_live_smoke(self):
        wf=(ROOT/".github/workflows/deploy-iteration32-test.yml").read_text()
        self.assertIn("actions/deploy-pages@v4", wf)
        self.assertIn("Greenfield Contracts", wf)
        self.assertIn("workflow_run", wf)
        self.assertIn("live-smoke", wf)
        self.assertIn("Mobile Safari", wf)
        self.assertNotIn("site/command-center", wf)
        self.assertNotIn("Daily-AI-Brief", wf.replace("New-Daily-AI-Brief",""))

if __name__ == "__main__":
    unittest.main()
