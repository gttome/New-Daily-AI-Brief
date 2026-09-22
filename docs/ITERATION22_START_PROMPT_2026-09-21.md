# Iteration 22 — Ready-to-Paste Start Prompt

> **ACTIVATION STATUS: READY.** Iteration 21 closure is reconciled on verified `main`; repository evidence reports `repository_closure_status=complete` and `iteration22_ready=true`. The receiving chat must still independently verify the current `main` SHA and CI before changing anything.

@GitHub Proceed with Iteration 22 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 21 is completely closed and passing, and read:

- `docs/ITERATION22_HANDOFF_2026-09-21.md`
- `docs/ITERATION21_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration21/synthetic-shadow-production-integration-execution-executor-binding-preflight-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 22 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 21 evidence reports a pending closure package or `iteration22_ready=false`. Establish the starting baseline only from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–21 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, and the exact locked Iteration 21 `production-integration-execution-executor-binding-preflight` artifact with its exact `executor_binding_preflight_id`, policy/manifest identity, separate preflight identity, synthetic binding-plan descriptor identity, exact executor-binding-preflight provenance-validation identities, exact Iteration 20 executor-binding-readiness binding/provenance identities, and all required transitive Iteration 19/18/17/16/15/14/13/12/11/10/9 identities.

Implement Iteration 22 only: a deterministic, synthetic-only production-integration execution executor-binding rehearsal gate from the exact locked Iteration 21 executor-binding-preflight artifact.

Build one versioned content-addressed `production-integration-execution-executor-binding-rehearsal` artifact, or the exact equivalent required by the handoff, that directly binds the exact Iteration 21 artifact digest and `executor_binding_preflight_id`, its policy/manifest/separate-preflight/synthetic-binding-plan identities, exact executor-binding-preflight provenance-validation set, exact Iteration 20 executor-binding-readiness identities, and every required upstream identity.

The current repository must remain `blocked` because its locked Iteration 21 executor-binding-preflight artifact is blocked. Do not infer rehearsal completion, actual executor identity, production authority, credentials, target service/environment, rollback authority, cost approval, cutover/decommission/publication approval, or any missing identity from chat or prior conversations.

A fully qualified synthetic `executor_binding_preflight_qualified` Iteration 21 fixture may be classified `executor_binding_rehearsal_complete` only with a separate explicit synthetic executor-binding-rehearsal decision/record and a complete deterministic ordered no-op receipt set covering the locked binding plan. Every receipt must be separately digestible, position-bound, `noop_verified=true`, `side_effect_free_verified=true`, and prove no real executor binding/invocation, no credential use, no target contact, no network side effect, no production write, no rollback/cutover/decommission/publication execution, and no external mutation.

This is rehearsal only: it must not bind or invoke a real executor, use credentials, contact a real target, grant production authority, perform rollback, deploy, publish, cut over, decommission, or mutate any external surface. All production/cutover/decommission/publication/executor/credential/target/rollback authorization flags must remain false.

Add one bounded executor-binding-rehearsal-only path through the existing canonical owner, such as `integration_execution_executor_binding_rehearsal_only=True`. Do not introduce a second orchestrator.

Prove deterministic replay, exact Iteration 21 and upstream binding, stable classifications/reason codes, stable ordered rehearsal receipt identities, fail-closed stale/corrupted Iteration 21 input, fail-closed reordered/duplicated/missing/corrupted Iteration 21 provenance, fail-closed reordered/duplicated/missing/substituted/corrupted rehearsal receipts, fail-closed unsupported Iteration 22 versions, fail-closed changed Iteration 21/22 identities, proof that `executor_binding_preflight_qualified` alone is insufficient without the separate rehearsal record and complete no-op receipt set, proof that any real endpoint/binding capability/invocation capability/executable command/executable step/credential/target/authority/mutation flag fails closed, targeted evaluation recovery, targeted mid-sequence receipt recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, zero reexecution of locked Iterations 1–21 work, zero Iteration 21 artifact rebuild, zero unrelated receipt rewrites, and zero full-pipeline restart.

Do not implement, bind, or invoke a real production executor. Do not use or store production credentials, contact a real target, grant actual production execution authority, perform rollback execution, mutate the real/private Command Center, implement final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Any such requirement without explicit repository-authoritative zero-cost approval must fail closed.

Do not stop for routine engineering decisions. Continue through implementation, deterministic replay, injected-failure recovery, full regression testing, PR/CI validation, merge, and independent post-merge `main` verification.

Iteration 22 is complete only after three consecutive synthetic/shadow executor-binding-rehearsal-only runs independently satisfy the handoff exit gate. Merge only the exact candidate that passes the complete regression and Iteration 22 suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION22_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 22 evidence under `evidence/iteration22/`;
- authoritative Iteration 23 handoff;
- separate ready-to-paste Iteration 23 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, closure-document paths, and whether Iteration 23 is ready to begin.
