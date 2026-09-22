@GitHub Proceed with Iteration 25 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, independently verify the current main SHA and Greenfield Contracts CI, verify Iteration 24 is completely closed and passing, and read:

- `docs/ITERATION25_HANDOFF_2026-09-21.md`
- `docs/ITERATION24_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration24/synthetic-shadow-production-integration-execution-executor-binding-authorization-decision-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 25 handoff is the controlling implementation specification.

Do not begin implementation if Iteration 24 evidence reports `repository_closure_status=pending`, `iteration25_ready=false`, any required closure artifact is missing, or current main CI is not passing. Establish the starting baseline solely from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–24 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts and completion primitives.

Preserve the exact locked Iteration 24 `production-integration-execution-executor-binding-authorization-decision` artifact with its exact artifact digest, decision ID, policy/manifest/separate-decision identity, ordered ten-record decision-evidence IDs/digests and set digest; exact Iteration 23 authorization-review artifact/review identity and ordered review-evidence inventory; exact Iteration 22 rehearsal/policy/manifest/separate-rehearsal and ordered no-op receipt inventory; exact Iteration 21 executor-binding preflight and Iteration 20 executor-binding readiness identities; and every required transitive Iterations 19–9 identity.

Implement Iteration 25 only: a deterministic, synthetic-only **executor-binding authorization-package gate** consuming the exact locked Iteration 24 decision artifact.

Build one versioned content-addressed `production-integration-execution-executor-binding-authorization-package` artifact. At minimum support `blocked`, `executor_binding_authorization_package_complete`, and `invalid`. The current repository must remain blocked because the exact locked Iteration 24 source is blocked.

A fully qualified synthetic `executor_binding_authorization_decision_complete` source may reach package-complete only with a separate independently digestible synthetic authorization-package record explicitly binding the exact Iteration 24 decision and ordered evidence inventory plus all required upstream identities. The record must explicitly state synthetic-only, no-op, non-live, zero incremental cost, and no production, executor-binding, executor-invocation, credential-use, target-contact, rollback, cutover, decommission, publication or external-mutation authority.

Add one mutually exclusive bounded package-only path through the existing canonical owner, such as `integration_execution_executor_binding_authorization_package_only=True`. Do not introduce a second orchestrator and do not prepare, rebuild or reexecute prior gates.

Prove deterministic replay; exact source and transitive binding; stable classifications/reason codes; fail-closed stale/corrupted source; fail-closed reordered/duplicated/missing/substituted/corrupted decision evidence; fail-closed changed source/package identities; fail-closed unsupported versions; fail-closed real endpoint, executor binding/invocation capability, executable command/step, credential, target, authority/mutation flag or paid dependency without explicit repository-authoritative zero-cost approval; and proof that source decision-complete alone is insufficient without the separate package record.

Inject and recover from package evaluation, targeted package-evidence/validation and final artifact assembly failures. Every recovery must use a fresh engine with no chat state and prove zero locked Iterations 1–24 reexecution, zero Iteration 24 rebuild, reuse of durable earlier package evidence, zero unrelated rewrites and zero full-pipeline restart.

Do not implement, bind or invoke a real executor. Do not use/store production credentials, contact a real target, grant or execute production/rollback authority, mutate the private Command Center, implement final UI, deploy GitHub Pages/public ChatGPT Sites, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API or other incremental paid production dependency. Missing repository-authoritative zero-cost approval must fail closed.

Continue through implementation, deterministic replay, three independent synthetic/shadow package-only exit runs, injected-failure recovery, complete regression testing, exact-candidate PR/CI validation, guarded exact-head merge and independent post-merge main CI verification.

Finish by creating and merging all four mandatory Iteration 25 closure artifacts required by `docs/ITERATION_START_PACKAGE_STANDARD.md`, including the authoritative Iteration 26 handoff and separate ready-to-paste Iteration 26 start prompt. Reconcile closure after closure merge/main CI before reporting Iteration 26 ready.

Report final main SHA, implementation and closure PRs, exact candidate/tree identities, candidate/main/closure CI runs and test counts, three-run exit results, recovery/anti-rework proof, closure paths and whether Iteration 26 is ready.
