from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SELECTOR_PATH = ROOT / "scripts" / "select_validation.py"
MAP_PATH = ROOT / "config" / "test-impact-map.json"

spec = importlib.util.spec_from_file_location("select_validation", SELECTOR_PATH)
selector = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(selector)


class ValidationRoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.impact_map = json.loads(MAP_PATH.read_text(encoding="utf-8"))

    def classify(self, *paths: str):
        return selector.classify_paths(self.impact_map, list(paths))

    def test_documentation_only_change_is_bounded(self):
        result = self.classify("docs/README_EXAMPLE.md")
        self.assertEqual(result["development_suites"], ["closure-metadata"])
        self.assertEqual(result["integration_suites"], [])
        self.assertFalse(result["full_system_validation_requested"])

    def test_command_center_ui_change_selects_bounded_command_center_tests(self):
        result = self.classify("site/command-center/cc.css")
        self.assertIn("command-center", result["development_suites"])
        self.assertIn("command-center-integration", result["integration_suites"])
        self.assertNotIn("reader-history-parity", result["integration_suites"])

    def test_command_center_adapter_selects_schema_and_integration_cone(self):
        result = self.classify("scripts/build_command_center_snapshot.py")
        self.assertIn("command-center", result["development_suites"])
        self.assertIn("shared-contracts", result["development_suites"])
        self.assertIn("command-center-integration", result["integration_suites"])
        self.assertFalse(result["full_system_validation_requested"])

    def test_runengine_stage_selects_relevant_dependency_cone_only(self):
        result = self.classify("src/new_daily_ai_brief/editorial.py")
        self.assertIn("iteration-2", result["development_suites"])
        self.assertIn("iteration-1", result["development_suites"])
        self.assertIn("iteration-2", result["integration_suites"])
        self.assertNotIn("iteration-31", result["development_suites"])

    def test_unknown_material_path_fails_closed(self):
        with self.assertRaises(selector.UnmappedPathError):
            self.classify("new-runtime/unmapped_component.py")

    def test_full_system_validation_is_manual_only(self):
        text = (ROOT / ".github" / "workflows" / "full-system-validation.yml").read_text(encoding="utf-8")
        self.assertIn("name: Full System Validation", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertNotIn("\npull_request:", text)
        self.assertNotIn("\npush:", text)

    def test_manual_full_system_entry_point_can_select_comprehensive_suite(self):
        text = (ROOT / ".github" / "workflows" / "full-system-validation.yml").read_text(encoding="utf-8")
        self.assertIn("suite:", text)
        self.assertIn("- all", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertEqual(
            self.impact_map["full_system_validation"]["suite_inventory"],
            ["python-comprehensive", "reader-comprehensive", "command-center-comprehensive"],
        )

    def test_reader_preview_is_change_impact_gated(self):
        text = (ROOT / ".github" / "workflows" / "deploy-iteration32-test.yml").read_text(encoding="utf-8")
        self.assertIn("Determine reader-preview change scope", text)
        self.assertIn("select_validation.py", text)
        self.assertIn("needs: scope", text)
        self.assertIn("needs.scope.outputs.should_run == 'true'", text)
        self.assertIn('"reader-runtime"', text)
        self.assertIn('"reader-history"', text)

    def test_selector_cli_emits_bounded_scope(self):
        with tempfile.TemporaryDirectory() as td:
            changed = Path(td) / "changed-files.txt"
            output = Path(td) / "selection.json"
            changed.write_text("site/command-center/cc.css\n", encoding="utf-8")
            proc = subprocess.run(
                [sys.executable, str(SELECTOR_PATH), "--changed-file-list", str(changed), "--output", str(output)],
                cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            selection = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(selection["development_suites"], ["command-center", "command-center-runtime", "command-center-v2"])
            self.assertEqual(selection["integration_suites"], ["command-center-integration"])
            self.assertFalse(selection["full_system_validation_requested"])


if __name__ == "__main__":
    unittest.main()
