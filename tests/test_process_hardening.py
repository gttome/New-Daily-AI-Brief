from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_closure_metadata.py"


class ProcessHardeningTests(unittest.TestCase):
    def test_progress_record_has_resume_guards(self):
        data = json.loads((ROOT / "evidence" / "iteration31" / "progress.json").read_text())
        self.assertEqual(data["record_type"], "iteration-progress")
        self.assertEqual(data["iteration"], 31)
        self.assertEqual(data["resume_policy"]["reuse_existing_pr"], 89)
        self.assertTrue(data["resume_policy"]["reuse_exact_head_ci"])
        self.assertFalse(data["resume_policy"]["duplicate_pr_permitted"])
        self.assertFalse(data["resume_policy"]["duplicate_ci_for_same_head_permitted"])
        self.assertFalse(data["resume_policy"]["prior_iteration_rebuild_permitted"])

    def test_workflow_preserves_required_name_and_full_regression(self):
        text = (ROOT / ".github" / "workflows" / "ci.yml").read_text()
        self.assertIn("name: Greenfield Contracts", text)
        self.assertIn("python -m unittest discover -s tests -v", text)
        self.assertIn("docs/*|evidence/*", text)
        self.assertIn("validate_closure_metadata.py", text)

    def test_validator_rejects_executable_path_on_bounded_route(self):
        with tempfile.TemporaryDirectory() as td:
            changed = Path(td) / "changed.txt"
            changed.write_text("src/new_daily_ai_brief/engine.py\n")
            proc = subprocess.run(
                [
                    "python",
                    str(VALIDATOR),
                    "--changed-file-list",
                    str(changed),
                    "--base-ref",
                    "",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertNotEqual(proc.returncode, 0)

    def test_validator_accepts_current_progress_as_metadata(self):
        with tempfile.TemporaryDirectory() as td:
            changed = Path(td) / "changed.txt"
            changed.write_text("evidence/iteration31/progress.json\n")
            proc = subprocess.run(
                [
                    "python",
                    str(VALIDATOR),
                    "--changed-file-list",
                    str(changed),
                    "--base-ref",
                    "",
                ],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
