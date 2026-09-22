from __future__ import annotations
import json, tempfile, unittest
from copy import deepcopy
from pathlib import Path
from new_daily_ai_brief.contracts import FailureInjection
from new_daily_ai_brief.engine import RunEngine, start_daily_brief
from new_daily_ai_brief.integration_execution_authorization_decision import (
    IntegrationExecutionAuthorizationDecisionBoundaryFailure,
    IntegrationExecutionAuthorizationDecisionError,
)
from new_daily_ai_brief.store import digest, semantic_digest
import test_iteration16

class Iteration17ExecutionAuthorizationDecisionTest(unittest.TestCase):
    DATE="2026-09-22"

    def helper(self):
        return test_iteration16.Iteration16ExecutionAuthorizationReviewTest(
            methodName="test_current_blocked_rehearsal_remains_blocked"
        )

    def fixture(self,name):
        return Path(__file__).resolve().parents[1]/"fixtures"/"iteration17"/name

    def make_review(self,root,date=DATE,mode="synthetic",ready=False):
        h=self.helper()
        _,engine=h.make_rehearsal(root,date,mode,rehearsal_complete=ready)
        kw={}
        if ready:
            kw["integration_execution_authorization_review_fixture_root"]=h.write_fixture(
                Path(root)/"i16-ready",engine
            )
        run=start_daily_brief(
            date,mode=mode,state_root=root,
            integration_execution_authorization_review_only=True,**kw
        )
        return deepcopy(run["stage_executions"]),RunEngine(root,date,mode=mode)

    def locked(self,engine):
        x=self.helper().locked_digests(engine)
        x["production-integration-execution-authorization-review"]=engine.store.load_artifact(
            "production-integration-execution-authorization-review"
        )["content_digest"]
        return x

    def write_fixture(self,root,engine,include_decision=True,mutate_policy=None,mutate_manifest=None):
        root.mkdir(parents=True,exist_ok=True); src=self.fixture("synthetic-authorization-decision-ready")
        p=json.loads((src/"authorization-decision-policy.json").read_text())
        m=json.loads((src/"authorization-decision-manifest.json").read_text())
        d=json.loads((src/"authorization-decision-record.json").read_text())
        review=engine.store.load_artifact("production-integration-execution-authorization-review"); rd=review["data"]
        vs=rd["receipt_verifications"]
        m["authorization_review_binding"].update({
            "authorization_review_artifact_digest":review["content_digest"],
            "authorization_review_id":rd["authorization_review_id"],
            "authorization_review_policy_id":rd["authorization_review_policy_id"],
            "authorization_review_policy_digest":rd["authorization_review_policy_digest"],
            "authorization_review_manifest_id":rd["authorization_review_manifest_id"],
            "authorization_review_manifest_digest":rd["authorization_review_manifest_digest"],
            "authorization_review_decision_id":rd["authorization_review_decision_id"],
            "authorization_review_decision_digest":rd["authorization_review_decision_digest"],
            "review_receipt_verification_ids":[x["verification_id"] for x in vs],
            "review_receipt_verification_digests":[digest(x) for x in vs],
            "review_receipt_verification_set_digest":digest(vs),
        })
        d.update({
            "authorization_review_id":rd["authorization_review_id"],
            "authorization_review_artifact_digest":review["content_digest"],
            "authorization_review_policy_id":rd["authorization_review_policy_id"],
            "authorization_review_policy_digest":rd["authorization_review_policy_digest"],
            "authorization_review_manifest_id":rd["authorization_review_manifest_id"],
            "authorization_review_manifest_digest":rd["authorization_review_manifest_digest"],
            "authorization_review_decision_id":rd["authorization_review_decision_id"],
            "authorization_review_decision_digest":rd["authorization_review_decision_digest"],
            "review_receipt_verification_set_digest":digest(vs),
        })
        if mutate_policy: mutate_policy(p)
        if mutate_manifest: mutate_manifest(m)
        body=deepcopy(d); body.pop("decision_id",None); d["decision_id"]=digest(body)
        (root/"authorization-decision-policy.json").write_text(json.dumps(p))
        (root/"authorization-decision-manifest.json").write_text(json.dumps(m))
        if include_decision:
            (root/"authorization-decision-record.json").write_text(json.dumps(d))
        return root

    def data(self,root,date=DATE,mode="synthetic"):
        return RunEngine(root,date,mode=mode).store.load_artifact(
            "production-integration-execution-authorization-decision"
        )["data"]

    def safe(self,d):
        flags=("production_action_authorized","production_cutover_authorized",
        "legacy_decommission_authorized","production_publication",
        "real_executor_invocation_authorized","credentials_use_authorized",
        "real_target_contact_authorized","rollback_execution_authorized",
        "real_private_command_center_mutated","public_site_mutated",
        "production_schedule_action","subscriber_delivery_changed",
        "legacy_content_migrated","readers_routed_to_greenfield",
        "legacy_repository_modified","incremental_paid_dependency_added",
        "lifecycle_state_changed")
        self.assertTrue(all(d[x] is False for x in flags))
        self.assertEqual((d["real_integration_steps_enabled"],d["real_integration_steps_executed"]),(0,0))
        self.assertTrue(all(x["enabled"] is False for x in d["execution_steps"]))

    def test_current_repository_stays_blocked_without_rework(self):
        with tempfile.TemporaryDirectory() as td:
            counts,e=self.make_review(td); digs=self.locked(e)
            run=start_daily_brief(self.DATE,state_root=td,integration_execution_authorization_decision_only=True)
            d=self.data(td)
            self.assertEqual(d["classification"],"blocked")
            self.assertEqual(d["classification_reason_codes"][0],"ITERATION16_AUTHORIZATION_REVIEW_BLOCKED")
            self.assertEqual(d["provenance_validation_ids"],[])
            self.assertEqual(self.locked(RunEngine(td,self.DATE)),digs)
            for k,v in counts.items(): self.assertEqual(run["stage_executions"].get(k),v)
            self.safe(d)

    def test_review_ready_requires_separate_decision_then_becomes_decision_ready(self):
        with tempfile.TemporaryDirectory() as td:
            _,e=self.make_review(td,ready=True)
            missing=self.write_fixture(Path(td)/"missing",e,include_decision=False)
            start_daily_brief(self.DATE,state_root=td,
                integration_execution_authorization_decision_fixture_root=missing,
                integration_execution_authorization_decision_only=True)
            self.assertEqual(self.data(td)["classification_reason_codes"],["AUTHORIZATION_DECISION_RECORD_MISSING"])
        with tempfile.TemporaryDirectory() as td:
            counts,e=self.make_review(td,ready=True); digs=self.locked(e)
            f=self.write_fixture(Path(td)/"ready",e)
            run=start_daily_brief(self.DATE,state_root=td,
                integration_execution_authorization_decision_fixture_root=f,
                integration_execution_authorization_decision_only=True)
            d=self.data(td)
            self.assertEqual(d["classification"],"authorization_decision_ready")
            self.assertEqual(d["classification_reason_codes"],["SYNTHETIC_AUTHORIZATION_DECISION_READY"])
            self.assertEqual(len(d["review_receipt_verification_ids"]),10)
            self.assertEqual(len(d["provenance_validation_ids"]),10)
            self.assertEqual(self.locked(RunEngine(td,self.DATE)),digs)
            for k,v in counts.items(): self.assertEqual(run["stage_executions"].get(k),v)
            self.safe(d)

    def test_exact_iteration16_and_transitive_identity_binding_and_replay(self):
        with tempfile.TemporaryDirectory() as td:
            _,e=self.make_review(td,ready=True); f=self.write_fixture(Path(td)/"bind",e)
            kw=dict(state_root=td,integration_execution_authorization_decision_fixture_root=f,
                    integration_execution_authorization_decision_only=True)
            start_daily_brief(self.DATE,**kw); first=RunEngine(td,self.DATE).store.load_artifact(
                "production-integration-execution-authorization-decision")
            review=RunEngine(td,self.DATE).store.load_artifact("production-integration-execution-authorization-review"); rd=review["data"]; d=first["data"]
            keys=("authorization_review_id","authorization_review_policy_id","authorization_review_policy_digest",
                  "authorization_review_manifest_id","authorization_review_manifest_digest",
                  "authorization_review_decision_id","authorization_review_decision_digest",
                  "execution_rehearsal_id","execution_attempt_id","execution_preflight_id","admission_id",
                  "plan_id","plan_graph_digest","dry_run_assertion_set_digest","rollback_boundary_set_digest",
                  "preflight_id","readiness_assessment_id","final_completion_receipt_digest","canonical_chain_digest")
            self.assertEqual(d["authorization_review_artifact_digest"],review["content_digest"])
            for k in keys: self.assertEqual(d[k],rd[k])
            start_daily_brief(self.DATE,**kw); second=RunEngine(td,self.DATE).store.load_artifact(
                "production-integration-execution-authorization-decision")
            self.assertEqual(first["content_digest"],second["content_digest"])
            self.assertEqual(first["data"],second["data"])

    def test_fail_closed_identity_verification_version_authority_step_and_cost(self):
        cases=("corrupt-review","reorder","duplicate","bad-policy","changed-binding","authority","step","cost","changed-decision")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as td:
                _,e=self.make_review(td,ready=True)
                if case in {"corrupt-review","reorder","duplicate","step"}:
                    r=e.store.load_artifact("production-integration-execution-authorization-review")
                    if case=="corrupt-review": r["data"]["authorization_review_policy_id"]="changed"
                    elif case=="reorder": r["data"]["receipt_verifications"].reverse()
                    elif case=="duplicate": r["data"]["receipt_verifications"][1]=deepcopy(r["data"]["receipt_verifications"][0])
                    else: r["data"]["execution_steps"][0]["enabled"]=True
                    r["content_digest"]=semantic_digest(r); e.store._atomic_write(e.store.artifact_path(
                        "production-integration-execution-authorization-review"),r)
                    f=None
                else:
                    pm=None; mm=None
                    if case=="bad-policy": pm=lambda p:p.update({"authorization_decision_policy_version":"2.0.0"})
                    if case=="changed-binding": mm=lambda m:m["authorization_review_binding"].update({"authorization_review_manifest_id":"changed"})
                    if case=="authority": mm=lambda m:m["evidence"]["authority_state"].update({"real_target_contact_authorized":True})
                    if case=="cost": mm=lambda m:m["evidence"]["cost_declaration"].update({"incremental_paid_dependency_required":True,"zero_incremental_cost_approved":False})
                    f=self.write_fixture(Path(td)/case,e,mutate_policy=pm,mutate_manifest=mm)
                    if case=="changed-decision":
                        p=f/"authorization-decision-record.json"; x=json.loads(p.read_text()); x["authorization_review_id"]="changed"; p.write_text(json.dumps(x))
                with self.assertRaises(IntegrationExecutionAuthorizationDecisionError):
                    start_daily_brief(self.DATE,state_root=td,
                        integration_execution_authorization_decision_fixture_root=f,
                        integration_execution_authorization_decision_only=True)

    def recovery(self,boundary):
        td=tempfile.TemporaryDirectory(); root=td.name
        counts,e=self.make_review(root,ready=True); digs=self.locked(e); f=self.write_fixture(Path(root)/"recovery",e)
        failing=RunEngine(root,self.DATE,failure_injection=FailureInjection("Complete","synthetic_i17_failure",boundary),
            integration_execution_authorization_decision_fixture_root=f,
            integration_execution_authorization_decision_only=True)
        with self.assertRaises(IntegrationExecutionAuthorizationDecisionBoundaryFailure): failing.run()
        start_daily_brief(self.DATE,state_root=root,
            integration_execution_authorization_decision_fixture_root=f,
            integration_execution_authorization_decision_only=True)
        fresh=RunEngine(root,self.DATE)
        self.assertEqual(self.locked(fresh),digs)
        for k,v in counts.items(): self.assertEqual(fresh.store.load_run()["stage_executions"].get(k),v)
        self.assertEqual(fresh.store.read_json(fresh.store.run_dir/"authorization-decision-incident.json")["result"],"recovered")
        return td,fresh

    def test_targeted_failure_recovery_and_fresh_engine_resume(self):
        td,e=self.recovery("authorization_decision:evaluation")
        self.assertEqual(e.store.read_json(e.store.run_dir/"authorization-decision-state.json")["attempts"]["evaluation"],2); td.cleanup()
        td,e=self.recovery("authorization_decision:verification:5")
        s=e.store.read_json(e.store.run_dir/"authorization-decision-state.json")
        self.assertGreaterEqual(s["metrics"]["provenance_validation_reuse"],4); self.assertEqual(len(self.data(td.name)["provenance_validation_ids"]),10); td.cleanup()
        td,e=self.recovery("authorization_decision:final_authorization_decision_artifact")
        s=e.store.read_json(e.store.run_dir/"authorization-decision-state.json")
        self.assertEqual(s["attempts"]["artifact_assembly"],2); self.assertGreaterEqual(s["metrics"]["provenance_validation_reuse"],10); td.cleanup()

    def test_bounded_exclusive_production_fail_closed_and_schema(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception): start_daily_brief(self.DATE,state_root=td,integration_execution_authorization_decision_only=True)
            with self.assertRaises(ValueError): RunEngine(td,self.DATE,
                integration_execution_authorization_review_only=True,
                integration_execution_authorization_decision_only=True)
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(Exception): start_daily_brief(self.DATE,mode="production",state_root=td,
                integration_execution_authorization_decision_only=True)
        s=json.loads((Path(__file__).resolve().parents[1]/"schemas"/
            "production-integration-execution-authorization-decision.schema.json").read_text())
        for k in ("production_action_authorized","production_cutover_authorized","legacy_decommission_authorized",
                  "production_publication","real_executor_invocation_authorized","credentials_use_authorized",
                  "real_target_contact_authorized","rollback_execution_authorized"):
            self.assertFalse(s["properties"][k]["const"])

    def test_three_run_exit_gate_and_three_ready_proofs(self):
        blocked=[]
        for date in ("2026-09-22","2026-09-23","2026-09-24"):
            with tempfile.TemporaryDirectory() as td:
                counts,e=self.make_review(td,date,"shadow"); digs=self.locked(e)
                run=start_daily_brief(date,mode="shadow",state_root=td,integration_execution_authorization_decision_only=True)
                d=self.data(td,date,"shadow"); self.safe(d)
                self.assertEqual(self.locked(RunEngine(td,date,mode="shadow")),digs)
                for k,v in counts.items(): self.assertEqual(run["stage_executions"].get(k),v)
                blocked.append((d["classification"],tuple(d["classification_reason_codes"])))
        self.assertEqual(blocked[0],blocked[1]); self.assertEqual(blocked[1],blocked[2])
        ready=[]
        for date in ("2026-09-25","2026-09-26","2026-09-27"):
            with tempfile.TemporaryDirectory() as td:
                _,e=self.make_review(td,date,"shadow",True); f=self.write_fixture(Path(td)/"ready",e)
                start_daily_brief(date,mode="shadow",state_root=td,
                    integration_execution_authorization_decision_fixture_root=f,
                    integration_execution_authorization_decision_only=True)
                d=self.data(td,date,"shadow"); self.safe(d)
                self.assertEqual(d["classification"],"authorization_decision_ready")
                self.assertTrue(d["separate_authorization_decision_id"].startswith("sha256:"))
                ready.append((d["classification"],tuple(d["classification_reason_codes"])))
        self.assertEqual(ready[0],ready[1]); self.assertEqual(ready[1],ready[2])

if __name__=="__main__": unittest.main()
