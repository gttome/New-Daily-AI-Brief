@GitHub Proceed with Iteration 27 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use current `main` as the source of truth. Before changing anything, independently verify current main SHA and Greenfield Contracts CI, verify Iteration 26 is completely closed and passing, and read:

* `docs/ITERATION27_HANDOFF_2026-09-21.md`
* `docs/ITERATION26_AFTER_ACTION_2026-09-21.md`
* `evidence/iteration26/synthetic-shadow-production-integration-execution-executor-binding-authorization-package-readiness-evidence.json`
* `docs/SCHEMA_VERSION_POLICY.md`
* `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 27 handoff is controlling. Do not begin if Iteration 26 reports `repository_closure_status=pending`, `iteration27_ready=false`, required closure records are missing, or current main CI is not passing. Establish the baseline only from reconciled repository records, never chat history.

Preserve the Iterations 1–26 lifecycle, state machine, canonical `start_daily_brief(date, mode)`, single `RunEngine` owner, lease/idempotency, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, exact locked Iteration 26 readiness identity/evidence inventory, exact Iteration 25 authorization-package identity/evidence inventory, exact Iteration 24 decision identity/evidence inventory, and every required transitive identity. Do not rebuild or reexecute completed gates.

Implement Iteration 27 only: the deterministic synthetic-only executor-binding authorization-package-readiness preflight gate defined in the handoff. Keep the current repository blocked. Require a separate independently digestible preflight record for any synthetic preflight-complete proof. Add one mutually exclusive bounded preflight-only path through the canonical owner; do not introduce a second orchestrator.

Prove deterministic replay, exact source/transitive binding, all required fail-closed cases, three independent shadow exit runs, and fresh-engine recovery from evaluation, targeted preflight-evidence validation, and final artifact assembly with zero Iterations 1–26 reexecution, zero Iteration 26 rebuild, durable evidence reuse, zero unrelated rewrites, and zero full-pipeline restart.

Do not implement/bind/invoke a real executor, use/store production credentials, contact a real target, grant/execute production or rollback authority, mutate the private Command Center, implement final UI, deploy Pages/Sites, change public URLs, perform real public-route verification, create/modify/run production schedules, change subscriber delivery, migrate/cut over/decommission legacy, publish to production, modify `gttome/Daily-AI-Brief`, or add separately billed/incremental paid dependencies. Missing repository-authoritative zero-cost approval must fail closed.

Continue through implementation, complete regression testing, exact-candidate PR/CI, guarded exact-head merge and independent post-merge main CI. Then create and merge all four mandatory Iteration 27 closure artifacts required by `docs/ITERATION_START_PACKAGE_STANDARD.md`, including the authoritative Iteration 28 handoff and standalone ready-to-paste Iteration 28 start prompt. Reconcile closure after closure merge/main CI before reporting Iteration 28 ready.

Report final main SHA, implementation and closure PRs, exact candidate/tree identities, candidate/main/closure CI runs and test counts, three-run exit results, recovery/anti-rework proof, closure paths, and whether Iteration 28 is ready.
