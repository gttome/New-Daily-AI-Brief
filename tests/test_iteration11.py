from __future__ import annotations

import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_preflight import (
    IntegrationPreflightBoundaryFailure,
    IntegrationPreflightError,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration10


class Iteration11IntegrationPreflightTest(unittest.TestCase):
    DATE = "2026-09-22"
    UNRESOLVED_CODES = [
        "COST_POLICY_RESOLUTION_MISSING",
        "PRODUCTION_DISCOVERY_RESOLUTION_MISSING",
        "PRODUCTION_PUBLICATION_RESOLUTION_MISSING",
        "PUBLIC_DEPLOYMENT_VERIFICATION_RESOLUTION_MISSING",
        "PRIVATE_COMMAND_CENTER_RESOLUTION_MISSING",
        "PRODUCTION_SCHEDULES_RESOLUTION_MISSING",
        "LEGACY_MIGRATION_CUTOVER_RESOLUTION_MISSING",
        "ROLLBACK_RECOVERY_RESOLUTION_MISSING",
    ]

    def helper(self):
        return test_iteration10.Iteration10ReadinessTest(
            methodName="test_current_live_capability_configuration_is_deterministically_blocked"
        )

    def fixture(self, name: str) -> Path:
        return Path(__file__).resolve().parents[1] / "fixtures" / "iteration11" / name

    def ready(self, root: str, edition_date: str = DATE, mode: str = "synthetic"):
        before_counts, _, _, _ = self.helper().complete(root, edition_date, mode)
        run = start_daily_brief(edition_date, mode=mode, state_root=root, readiness_only=True)
        engine = RunEngine(root, edition_date, mode=mode)
        return deepcopy(run["stage_executions"]), engine

    def locked_digests(self, engine: RunEngine):
        values = self.helper().locked_digests(engine)
        values["readiness-admission"] = engine.store.load_artifact("readiness-admission")[
            "content_digest"
        ]
        return values

    def readiness_semantic_identity(self, data: dict):
        return {
            "readiness_schema_version": data.get("readiness_schema_version"),
            "readiness_policy_version": data.get("readiness_policy_version"),
            "policy_id": data.get("policy_id"),
            "profile_id": data.get("profile_id"),
            "completion_artifact_digest": data.get("completion_artifact_digest"),
            "final_completion_receipt_digest": data.get("final_completion_receipt_digest"),
            "canonical_chain_digest": data.get("canonical_chain_digest"),
            "policy_digest": data.get("policy_digest"),
            "capability_digest": data.get("capability_digest"),
            "classification": data.get("classification"),
            "prerequisite_results": data.get("prerequisite_results") or [],
            "blocker_reason_codes": data.get("blocker_reason_codes") or [],
        }

    def test_current_repository_configuration_remains_unresolved(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.ready(td)
            before_digests = self.locked_digests(engine)
            result = start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            final = RunEngine(td, self.DATE)
            artifact = final.store.load_artifact("production-integration-preflight")
            data = artifact["data"]
            self.assertEqual(result["current_state"], "Complete")
            self.assertEqual(result["completion_status"], "complete_locked")
            self.assertEqual(data["classification"], "unresolved")
            self.assertEqual(len(data["resolution_results"]), 10)
            self.assertEqual(data["unresolved_reason_codes"], self.UNRESOLVED_CODES)
            self.assertEqual(
                [x["resolution_state"] for x in data["resolution_results"]].count("resolved"),
                2,
            )
            self.assertEqual(
                [x["resolution_state"] for x in data["resolution_results"]].count("unresolved"),
                8,
            )
            self.assertFalse(data["production_action_authorized"])
            self.assertFalse(data["production_cutover_authorized"])
            self.assertFalse(data["legacy_decommission_authorized"])
            self.assertFalse(data["production_publication"])
            self.assertEqual(self.locked_digests(final), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(result["stage_executions"].get(stage), count)

    def test_fully_qualified_synthetic_manifest_is_logically_qualified_only(self):
        with tempfile.TemporaryDirectory() as td:
            self.ready(td)
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_preflight_fixture_root=self.fixture("synthetic-qualified"),
                integration_preflight_only=True,
            )
            engine = RunEngine(td, self.DATE)
            data = engine.store.load_artifact("production-integration-preflight")["data"]
            self.assertEqual(data["classification"], "qualified")
            self.assertEqual(data["unresolved_reason_codes"], [])
            self.assertEqual(data["invalid_reason_codes"], [])
            self.assertTrue(data["synthetic_only"])
            self.assertTrue(all(x["resolution_state"] == "resolved" for x in data["resolution_results"]))
            self.assertFalse(data["production_action_authorized"])
            self.assertFalse(data["production_cutover_authorized"])
            self.assertFalse(data["legacy_decommission_authorized"])
            self.assertFalse(data["production_publication"])

    def test_preflight_identity_is_deterministic_and_replay_reuses_one_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            self.ready(td)
            first = start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            engine = RunEngine(td, self.DATE)
            artifact1 = engine.store.load_artifact("production-integration-preflight")
            counts = deepcopy(first["stage_executions"])
            second = start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            artifact2 = engine.store.load_artifact("production-integration-preflight")
            self.assertEqual(artifact2["content_digest"], artifact1["content_digest"])
            self.assertEqual(artifact2["data"]["preflight_id"], artifact1["data"]["preflight_id"])
            self.assertEqual(second["stage_executions"], counts)

    def test_preflight_binds_exact_iteration10_readiness_identity(self):
        with tempfile.TemporaryDirectory() as td:
            self.ready(td)
            start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            engine = RunEngine(td, self.DATE)
            readiness = engine.store.load_artifact("readiness-admission")
            preflight = engine.store.load_artifact("production-integration-preflight")["data"]
            self.assertEqual(preflight["readiness_artifact_digest"], readiness["content_digest"])
            self.assertEqual(preflight["readiness_assessment_id"], readiness["data"]["assessment_id"])
            self.assertEqual(preflight["completion_artifact_digest"], readiness["data"]["completion_artifact_digest"])
            self.assertEqual(
                preflight["final_completion_receipt_digest"],
                readiness["data"]["final_completion_receipt_digest"],
            )

    def test_preflight_does_not_reexecute_iteration10_readiness(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.ready(td)
            readiness_state_path = engine.store.run_dir / "iteration10-readiness-state.json"
            readiness_state_before = engine.store.read_json(readiness_state_path)
            readiness_digest = engine.store.load_artifact("readiness-admission")["content_digest"]
            run = start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            readiness_state_after = engine.store.read_json(readiness_state_path)
            self.assertEqual(
                readiness_state_after["attempts"]["policy_evaluation"],
                readiness_state_before["attempts"]["policy_evaluation"],
            )
            self.assertEqual(
                engine.store.load_artifact("readiness-admission")["content_digest"], readiness_digest
            )
            for stage, count in before_counts.items():
                self.assertEqual(run["stage_executions"].get(stage), count)

    def test_resolution_evaluation_failure_recovers_on_fresh_engine_without_rework(self):
        with tempfile.TemporaryDirectory() as td:
            before_counts, engine = self.ready(td)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_resolution_evaluation_failure",
                    "preflight:resolution_evaluation",
                ),
                integration_preflight_only=True,
            )
            with self.assertRaises(IntegrationPreflightBoundaryFailure):
                failing.run()
            self.assertIsNone(failing.store.load_artifact("production-integration-preflight"))
            recovered = start_daily_brief(
                self.DATE, state_root=td, integration_preflight_only=True
            )
            fresh = RunEngine(td, self.DATE)
            state = fresh.store.read_json(fresh.store.run_dir / "iteration11-preflight-state.json")
            incident = fresh.store.read_json(
                fresh.store.run_dir / "iteration11-preflight-incident.json"
            )
            self.assertEqual(state["attempts"]["resolution_evaluation"], 2)
            self.assertEqual(incident["result"], "recovered")
            self.assertEqual(incident["recovery_receipt"]["boundary_id"], "resolution_evaluation")
            self.assertEqual(self.locked_digests(fresh), before_digests)
            for stage, count in before_counts.items():
                self.assertEqual(recovered["stage_executions"].get(stage), count)

    def test_final_preflight_artifact_failure_recovers_and_reuses_resolution_decisions(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.ready(td)
            before_digests = self.locked_digests(engine)
            failing = RunEngine(
                td,
                self.DATE,
                failure_injection=FailureInjection(
                    "Complete",
                    "synthetic_final_preflight_failure",
                    "preflight:final_preflight_artifact",
                ),
                integration_preflight_only=True,
            )
            with self.assertRaises(IntegrationPreflightBoundaryFailure):
                failing.run()
            state1 = failing.store.read_json(
                failing.store.run_dir / "iteration11-preflight-state.json"
            )
            self.assertIsNotNone(state1["evaluation"])
            self.assertIsNone(failing.store.load_artifact("production-integration-preflight"))
            start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            fresh = RunEngine(td, self.DATE)
            state2 = fresh.store.read_json(fresh.store.run_dir / "iteration11-preflight-state.json")
            self.assertEqual(state2["attempts"]["artifact_assembly"], 2)
            self.assertGreaterEqual(state2["metrics"]["resolution_evaluation_reuse"], 1)
            self.assertEqual(self.locked_digests(fresh), before_digests)

    def test_corrupted_readiness_artifact_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.ready(td)
            readiness = engine.store.load_artifact("readiness-admission")
            readiness["data"]["profile_id"] = "corrupted-without-digest-update"
            engine.store._atomic_write(engine.store.artifact_path("readiness-admission"), readiness)
            with self.assertRaises(IntegrationPreflightError):
                start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            self.assertIsNone(engine.store.load_artifact("production-integration-preflight"))

    def test_changed_readiness_identity_fails_closed_instead_of_reusing_cached_preflight(self):
        with tempfile.TemporaryDirectory() as td:
            _, engine = self.ready(td)
            start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)
            readiness = engine.store.load_artifact("readiness-admission")
            readiness["data"]["profile_id"] = "changed-readiness-identity"
            readiness["data"]["assessment_id"] = digest(
                self.readiness_semantic_identity(readiness["data"])
            )
            readiness["content_digest"] = semantic_digest(readiness)
            engine.store._atomic_write(engine.store.artifact_path("readiness-admission"), readiness)
            with self.assertRaises(IntegrationPreflightError):
                start_daily_brief(self.DATE, state_root=td, integration_preflight_only=True)

    def test_changed_resolution_manifest_identity_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.ready(td)
            fixture = Path(td) / "mutable-preflight"
            fixture.mkdir()
            for name in ("preflight-policy.json", "resolution-manifest.json"):
                (fixture / name).write_text(
                    (self.fixture("current-unresolved") / name).read_text(), encoding="utf-8"
                )
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_preflight_fixture_root=fixture,
                integration_preflight_only=True,
            )
            manifest_path = fixture / "resolution-manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["manifest_id"] = "changed-resolution-manifest-identity"
            manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(IntegrationPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_preflight_fixture_root=fixture,
                    integration_preflight_only=True,
                )

    def test_unsupported_preflight_policy_or_schema_version_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            self.ready(td)
            fixture = Path(td) / "bad-policy"
            fixture.mkdir()
            policy = json.loads(
                (self.fixture("current-unresolved") / "preflight-policy.json").read_text()
            )
            manifest = json.loads(
                (self.fixture("current-unresolved") / "resolution-manifest.json").read_text()
            )
            policy["preflight_policy_version"] = "99.0.0"
            (fixture / "preflight-policy.json").write_text(json.dumps(policy))
            (fixture / "resolution-manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(IntegrationPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_preflight_fixture_root=fixture,
                    integration_preflight_only=True,
                )

        with tempfile.TemporaryDirectory() as td:
            self.ready(td)
            fixture = Path(td) / "bad-schema"
            fixture.mkdir()
            policy = json.loads(
                (self.fixture("current-unresolved") / "preflight-policy.json").read_text()
            )
            manifest = json.loads(
                (self.fixture("current-unresolved") / "resolution-manifest.json").read_text()
            )
            manifest["schema_version"] = "99.0.0"
            (fixture / "preflight-policy.json").write_text(json.dumps(policy))
            (fixture / "resolution-manifest.json").write_text(json.dumps(manifest))
            with self.assertRaises(IntegrationPreflightError):
                start_daily_brief(
                    self.DATE,
                    state_root=td,
                    integration_preflight_fixture_root=fixture,
                    integration_preflight_only=True,
                )

    def test_invalid_resolution_evidence_classifies_invalid_and_never_authorizes(self):
        with tempfile.TemporaryDirectory() as td:
            self.ready(td)
            fixture = Path(td) / "invalid-evidence"
            fixture.mkdir()
            policy = json.loads(
                (self.fixture("synthetic-qualified") / "preflight-policy.json").read_text()
            )
            manifest = json.loads(
                (self.fixture("synthetic-qualified") / "resolution-manifest.json").read_text()
            )
            manifest["resolutions"]["production_discovery"]["evidence"]["adapter_id"] = None
            (fixture / "preflight-policy.json").write_text(json.dumps(policy))
            (fixture / "resolution-manifest.json").write_text(json.dumps(manifest))
            start_daily_brief(
                self.DATE,
                state_root=td,
                integration_preflight_fixture_root=fixture,
                integration_preflight_only=True,
            )
            data = RunEngine(td, self.DATE).store.load_artifact(
                "production-integration-preflight"
            )["data"]
            self.assertEqual(data["classification"], "invalid")
            self.assertIn("PRODUCTION_DISCOVERY_RESOLUTION_INVALID", data["invalid_reason_codes"])
            self.assertFalse(data["production_action_authorized"])

    def test_three_consecutive_shadow_preflight_only_exit_gate_runs(self):
        observed_codes = []
        for edition_date in ("2026-09-22", "2026-09-23", "2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                before_counts, engine = self.ready(td, edition_date, mode="shadow")
                before_digests = self.locked_digests(engine)
                run = start_daily_brief(
                    edition_date,
                    mode="shadow",
                    state_root=td,
                    integration_preflight_only=True,
                )
                final = RunEngine(td, edition_date, mode="shadow")
                artifact = final.store.load_artifact("production-integration-preflight")
                data = artifact["data"]
                self.assertEqual(data["classification"], "unresolved")
                self.assertEqual(data["unresolved_reason_codes"], self.UNRESOLVED_CODES)
                self.assertFalse(data["production_action_authorized"])
                self.assertFalse(data["real_private_command_center_mutated"])
                self.assertFalse(data["public_site_mutated"])
                self.assertFalse(data["production_schedule_action"])
                self.assertFalse(data["legacy_content_migrated"])
                self.assertFalse(data["production_publication"])
                self.assertEqual(self.locked_digests(final), before_digests)
                for stage, count in before_counts.items():
                    self.assertEqual(run["stage_executions"].get(stage), count)
                observed_codes.append(data["unresolved_reason_codes"])
        self.assertEqual(observed_codes, [self.UNRESOLVED_CODES] * 3)

    def test_preflight_schema_exposes_all_classifications_and_non_authorization(self):
        schema = json.loads(
            (
                Path(__file__).resolve().parents[1]
                / "schemas"
                / "production-integration-preflight.schema.json"
            ).read_text()
        )
        self.assertEqual(
            schema["properties"]["classification"]["enum"],
            ["unresolved", "qualified", "invalid"],
        )
        self.assertFalse(schema["properties"]["production_action_authorized"]["const"])
        self.assertFalse(schema["properties"]["production_cutover_authorized"]["const"])
        self.assertFalse(schema["properties"]["legacy_decommission_authorized"]["const"])
        self.assertFalse(schema["properties"]["production_publication"]["const"])
        self.assertEqual(schema["properties"]["resolution_results"]["minItems"], 10)
        self.assertEqual(schema["properties"]["resolution_results"]["maxItems"], 10)


if __name__ == "__main__":
    unittest.main()
