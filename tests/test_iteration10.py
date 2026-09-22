from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.completion import CompletionBoundaryFailure
from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.readiness import ReadinessBoundaryFailure, ReadinessError
from new_daily_ai_brief.store import digest, semantic_digest
from test_iteration9 import Iteration9FinalCompletionTest


class Iteration10ReadinessTest(unittest.TestCase):
    DATE = "2026-09-22"
    BLOCKED_CODES = [
        "COST_POLICY_APPROVAL_MISSING",
        "DISCOVERY_ADAPTER_MISSING_OR_UNAPPROVED",
        "PUBLICATION_PATH_OR_TARGET_MISSING_OR_UNAPPROVED",
        "PUBLIC_DEPLOYMENT_OR_VERIFICATION_MISSING_OR_UNAPPROVED",
        "PRIVATE_COMMAND_CENTER_INTEGRATION_MISSING_OR_UNAPPROVED",
        "SCHEDULE_POLICY_MISSING_OR_UNAPPROVED",
        "MIGRATION_CUTOVER_PREREQUISITES_MISSING_OR_UNAPPROVED",
        "ROLLBACK_RECOVERY_MISSING_OR_UNAPPROVED",
    ]

    def helper(self):
        return Iteration9FinalCompletionTest(
            methodName="test_completion_binds_entire_locked_chain_and_is_nonproduction"
        )

    def complete(self, root: str, edition_date: str = DATE, mode: str = "synthetic"):
        return self.helper().complete(root, edition_date, mode)

    def fixture(self, name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration10" / name

    def locked_digests(self, engine: RunEngine):
        names = (*self.helper().LOCKED_ITERATION1_8, "completion")
        return {name: engine.store.load_artifact(name)["content_digest"] for name in names}

    def test_current_live_capability_configuration_is_deterministically_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, _, _, engine = self.complete(td)
            before_digests = self.locked_digests(engine)
            result = start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            final = RunEngine(td, self.DATE, readiness_only=True)
            data = final.store.load_artifact("readiness-admission")["data"]
            self.assertEqual(result["current_state"], "Complete")
            self.assertEqual(result["completion_status"], "complete_locked")
            self.assertEqual(data["classification"], "blocked")
            self.assertEqual(data["blocker_reason_codes"], self.BLOCKED_CODES)
            self.assertFalse(data["production_action_authorized"])
            self.assertTrue(data["synthetic_only"])
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(result["stage_executions"].get(stage), count)

    def test_fully_qualified_synthetic_fixture_is_admissible_but_never_authorized(self):
        with tempfile.TemporaryDirectory() as td:
            self.complete(td)
            start_daily_brief(
                self.DATE,
                state_root=td,
                readiness_fixture_root=self.fixture("synthetic-admissible"),
                readiness_only=True,
            )
            engine = RunEngine(
                td,
                self.DATE,
                readiness_fixture_root=self.fixture("synthetic-admissible"),
                readiness_only=True,
            )
            data = engine.store.load_artifact("readiness-admission")["data"]
            self.assertEqual(data["classification"], "admissible")
            self.assertEqual(data["blocker_reason_codes"], [])
            self.assertFalse(data["production_action_authorized"])
            self.assertFalse(data["production_cutover_authorized"])
            self.assertFalse(data["legacy_decommission_authorized"])
            self.assertFalse(data["production_publication"])

    def test_readiness_identity_is_deterministic_and_replay_reuses_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.complete(td)
            first = start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            artifact1 = engine.store.load_artifact("readiness-admission")
            counts = deepcopy(first["stage_executions"])
            second = start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            artifact2 = engine.store.load_artifact("readiness-admission")
            self.assertEqual(artifact2["content_digest"], artifact1["content_digest"])
            self.assertEqual(artifact2["data"]["assessment_id"], artifact1["data"]["assessment_id"])
            self.assertEqual(second["stage_executions"], counts)

    def test_readiness_binds_exact_completion_and_final_receipt_identity(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.complete(td)
            start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            completion = engine.store.load_artifact("completion")
            receipt = engine.store.read_json(
                engine.store.run_dir / "iteration9-final-completion-receipt.json"
            )
            data = engine.store.load_artifact("readiness-admission")["data"]
            self.assertEqual(data["completion_artifact_digest"], completion["content_digest"])
            self.assertEqual(data["final_completion_receipt_digest"], digest(receipt))
            self.assertEqual(data["canonical_chain_digest"], completion["data"]["canonical_chain_digest"])

    def test_policy_evaluation_failure_recovers_on_fresh_engine_without_upstream_rework(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, _, _, engine = self.complete(td)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_policy_evaluation_failure",
                    "readiness:policy_evaluation",
                ),
                readiness_only=True,
            )
            with self.assertRaises(ReadinessBoundaryFailure):
                failing.run()
            self.assertEqual(failing.store.load_run()["current_state"], "Complete")
            self.assertIsNone(failing.store.load_artifact("readiness-admission"))
            recovered = start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            fresh = RunEngine(td, self.DATE, readiness_only=True)
            state = fresh.store.read_json(fresh.store.run_dir / "iteration10-readiness-state.json")
            incident = fresh.store.read_json(fresh.store.run_dir / "iteration10-readiness-incident.json")
            self.assertEqual(state["attempts"]["policy_evaluation"], 2)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "policy_evaluation")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_final_artifact_failure_recovers_and_reuses_durable_policy_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.complete(td)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_final_readiness_failure",
                    "readiness:final_readiness_artifact",
                ),
                readiness_only=True,
            )
            with self.assertRaises(ReadinessBoundaryFailure):
                failing.run()
            state1 = failing.store.read_json(failing.store.run_dir / "iteration10-readiness-state.json")
            self.assertIsNotNone(state1["evaluation"])
            self.assertIsNone(failing.store.load_artifact("readiness-admission"))
            start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            fresh = RunEngine(td, self.DATE, readiness_only=True)
            state2 = fresh.store.read_json(fresh.store.run_dir / "iteration10-readiness-state.json")
            self.assertEqual(state2["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state2["metrics"]["policy_evaluation_reuse"], 1)
            self.assertEqual(self.locked_digests(fresh), before_digests)

    def test_corrupted_completion_and_final_receipt_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.complete(td)
            completion = engine.store.load_artifact("completion")
            completion["data"]["completion_scope"] = "corrupt"
            completion["content_digest"] = semantic_digest(completion)
            engine.store._atomic_write(engine.store.artifact_path("completion"), completion)
            with self.assertRaises((CompletionBoundaryFailure, ReadinessError)):
                start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            self.assertIsNone(engine.store.load_artifact("readiness-admission"))

        with tempfile.TemporaryDirectory() as td:
            _, _, _, engine = self.complete(td)
            path = engine.store.run_dir / "iteration9-final-completion-receipt.json"
            receipt = engine.store.read_json(path)
            receipt["final_status"] = "corrupt"
            engine.store._atomic_write(path, receipt)
            with self.assertRaises((CompletionBoundaryFailure, ReadinessError)):
                start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            self.assertIsNone(engine.store.load_artifact("readiness-admission"))

    def test_unsupported_policy_or_schema_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.complete(td)
            fixture = Path(td) / "bad-policy"
            fixture.mkdir()
            policy = json.loads((self.fixture("current-blocked") / "readiness-policy.json").read_text())
            capability = json.loads((self.fixture("current-blocked") / "capability-declaration.json").read_text())
            policy["readiness_policy_version"] = "99.0.0"
            (fixture / "readiness-policy.json").write_text(json.dumps(policy))
            (fixture / "capability-declaration.json").write_text(json.dumps(capability))
            with self.assertRaises(ReadinessError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    readiness_fixture_root=fixture,
                    readiness_only=True,
                )

        with tempfile.TemporaryDirectory() as td:
            self.complete(td)
            fixture = Path(td) / "bad-schema"
            fixture.mkdir()
            policy = json.loads((self.fixture("current-blocked") / "readiness-policy.json").read_text())
            capability = json.loads((self.fixture("current-blocked") / "capability-declaration.json").read_text())
            capability["schema_version"] = "99.0.0"
            (fixture / "readiness-policy.json").write_text(json.dumps(policy))
            (fixture / "capability-declaration.json").write_text(json.dumps(capability))
            with self.assertRaises(ReadinessError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    readiness_fixture_root=fixture,
                    readiness_only=True,
                )

    def test_changed_capability_identity_fails_closed_instead_of_reusing_cached_readiness(self):
        with tempfile.TemporaryDirectory() as td:
            self.complete(td)
            fixture = Path(td) / "mutable-fixture"
            fixture.mkdir()
            for name in ("readiness-policy.json", "capability-declaration.json"):
                (fixture / name).write_text((self.fixture("current-blocked") / name).read_text())
            start_daily_brief(
                self.DATE,
                state_root=td,
                readiness_fixture_root=fixture,
                readiness_only=True,
            )
            capability = json.loads((fixture / "capability-declaration.json").read_text())
            capability["profile_id"] = "changed-capability-identity"
            (fixture / "capability-declaration.json").write_text(json.dumps(capability))
            with self.assertRaises(ReadinessError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    readiness_fixture_root=fixture,
                    readiness_only=True,
                )

    def test_missing_cost_adapter_private_public_and_rollback_approvals_have_stable_codes(self):
        with tempfile.TemporaryDirectory() as td:
            self.complete(td)
            start_daily_brief(self.DATE, state_root=td, readiness_only=True)
            engine = RunEngine(td, self.DATE, readiness_only=True)
            blockers = engine.store.load_artifact("readiness-admission")["data"]["blocker_reason_codes"]
            self.assertIn("COST_POLICY_APPROVAL_MISSING", blockers)
            self.assertIn("DISCOVERY_ADAPTER_MISSING_OR_UNAPPROVED", blockers)
            self.assertIn("PRIVATE_COMMAND_CENTER_INTEGRATION_MISSING_OR_UNAPPROVED", blockers)
            self.assertIn("PUBLIC_DEPLOYMENT_OR_VERIFICATION_MISSING_OR_UNAPPROVED", blockers)
            self.assertIn("ROLLBACK_RECOVERY_MISSING_OR_UNAPPROVED", blockers)

    def test_three_consecutive_shadow_readiness_only_exit_gate_runs(self):
        observed_codes = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                before_counts, _, _, engine = self.complete(td, edition_date, mode="shadow")
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date, mode="shadow", state_root=td, readiness_only=True
                )
                final = RunEngine(td, edition_date, mode="shadow", readiness_only=True)
                artifact = final.store.load_artifact("readiness-admission")
                data = artifact["data"]
                self.assertEqual(data["classification"], "blocked")
                self.assertFalse(data["production_action_authorized"])
                self.assertFalse(data["real_private_command_center_mutated"])
                self.assertFalse(data["public_site_mutated"])
                self.assertFalse(data["production_schedule_action"])
                self.assertFalse(data["legacy_content_migrated"])
                self.assertFalse(data["production_publication"])
                self.assertEqual(self.locked_digests(final), before_digests)
                for stage, count in before_counts.items():
                    self.assertEqual(run["stage_executions"].get(stage), count)
                observed_codes.append(data["blocker_reason_codes"])
        self.assertEqual(observed_codes, [self.BLOCKED_CODES] * 3)

    def test_readiness_schema_exposes_all_classifications_and_non_authorization(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "readiness-admission.schema.json"
            ).read_text()
        )
        self.assertEqual(
            schema["properties"]["classification"]["enum"],
            ["admissible", "blocked", "invalid"],
        )
        self.assertFalse(schema["properties"]["production_action_authorized"]["const"])


if __name__ == "__main__":
    unittest.main()
