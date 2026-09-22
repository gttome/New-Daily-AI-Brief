# Iteration 21 — Ready-to-Paste Start Prompt

> **ACTIVATION STATUS: NOT READY.** Iteration 20 closure has not yet been reconciled in this initial closure package. Do not use this prompt until current repository evidence reports `repository_closure_status=complete` and `iteration21_ready=true`. Even then, re-verify current `main` and CI before changing anything.

@GitHub Proceed with Iteration 21 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 20 is completely closed and passing, and read:

- `docs/ITERATION21_HANDOFF_2026-09-21.md`
- `docs/ITERATION20_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration20/synthetic-shadow-production-integration-execution-executor-binding-readiness-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 21 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 20 evidence reports a pending closure package or `iteration21_ready=false`. Establish the starting baseline only from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–20 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, and the exact locked Iteration 20 `production-integration-execution-executor-binding-readiness` artifact with its exact `executor_binding_readiness_id`, policy/manifest identity, separate readiness identity, synthetic executor descriptor identity, exact executor-binding provenance-validation identities, exact Iteration 19 authority-readiness binding/provenance identities, and all required transitive Iteration 18/17/16/15/14/13/12/11/10/9 identities.

Implement Iteration 21 only: a deterministic, synthetic-only production-integration execution executor-binding preflight gate from the exact locked Iteration 20 executor-binding-readiness artifact.

Build one versioned content-addressed `production-integration-execution-executor-binding-preflight` artifact, or the exact equivalent required by the handoff, that directly binds the exact Iteration 20 artifact digest and `executor_binding_readiness_id`, its policy/manifest/separate-readiness/synthetic-executor-descriptor identities, exact executor-binding provenance-validation set, and every required upstream identity.

The current repository must remain `blocked` because its locked Iteration 20 executor-binding-readiness artifact is blocked. Do not infer preflight qualification, actual executor identity, production authority, credentials, target service/environment, rollback authority, cost approval, cutover/decommission/publication approval, or any missing identity from chat or prior conversations.

A fully qualified synthetic `executor_binding_ready` Iteration 20 fixture may be classified `executor_binding_preflight_qualified` only with a separate explicit synthetic executor-binding-preflight record, complete explicit preflight envelope, and separately digestible non-live synthetic binding-plan descriptor. This is preflight qualification only: it must not bind or invoke a real executor, use credentials, contact a real target, grant production authority, perform rollback, deploy, publish, cut over, decommission, or mutate any external surface. All production/cutover/decommission/publication/executor/credential/target/rollback authorization flags must remain false.

Add one bounded executor-binding-preflight-only path through the existing canonical owner, such as `integration_execution_executor_binding_preflight_only=True`. Do not introduce a second orchestrator.

Prove deterministic replay, exact Iteration 20 and upstream binding, stable classifications/reason codes, exact provenance validation, fail-closed stale/corrupted Iteration 20 input, fail-closed reordered/duplicated/corrupted provenance substitution, fail-closed unsupported Iteration 21 versions, fail-closed changed Iteration 20/21 identities, proof that `executor_binding_ready` alone is insufficient without the separate preflight record and synthetic binding-plan descriptor, proof that any real endpoint/binding or invocation capability/executable command/executable step/authority flag fails closed, targeted evaluation recovery, targeted provenance/binding-plan-validation recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, zero reexecution of locked Iterations 1–20 work, zero Iteration 20 artifact rebuild, and zero full-pipeline restart.

Do not implement, bind, or invoke a real production executor. Do not use or store production credentials, contact a real target, grant actual production execution authority, perform rollback execution, mutate the real/private Command Center, implement final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Any such requirement without explicit repository-authoritative zero-cost approval must fail closed.

Do not stop for routine engineering decisions. Continue through implementation, deterministic replay, injected-failure recovery, full regression testing, PR/CI validation, merge, and independent post-merge `main` verification.

Iteration 21 is complete only after three consecutive synthetic/shadow executor-binding-preflight-only runs independently satisfy the handoff exit gate. Merge only the exact candidate that passes the complete regression and Iteration 21 suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION21_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 21 evidence under `evidence/iteration21/`;
- authoritative Iteration 22 handoff;
- separate ready-to-paste Iteration 22 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, closure-document paths, and whether Iteration 22 is ready to begin.
