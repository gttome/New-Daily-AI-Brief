# Ready-to-Paste Iteration 15 Start Prompt

@GitHub Proceed with Iteration 15 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 14 is completely closed and passing, and read:

- `docs/ITERATION15_HANDOFF_2026-09-21.md`
- `docs/ITERATION14_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration14/synthetic-shadow-production-integration-execution-preflight-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 15 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 14 evidence reports a pending closure package or `iteration15_ready=false`. Establish the starting baseline only from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–14 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, and the exact locked Iteration 14 `production-integration-execution-preflight` artifact with all exact admission/plan/transitive bindings, execution-envelope identities, separate execution-envelope decision semantics, current blocked classification, stable reason codes, disabled real steps, and fixed non-production authorization flags.

Implement Iteration 15 only: a deterministic, synthetic-only production-integration execution rehearsal and execution-attempt contract from the exact locked Iteration 14 execution-preflight artifact.

Build one versioned content-addressed `production-integration-execution-rehearsal` artifact, or the equivalent required by the handoff, that directly binds the exact Iteration 14 artifact digest and `execution_preflight_id`, all execution-envelope identities, the Iteration 13 admission, Iteration 12 plan and ten-step graph, dry-run assertions, rollback boundaries, and all transitive upstream identities.

The current repository must remain `blocked` because its locked Iteration 14 execution preflight is blocked. Do not infer rehearsal authorization, executable steps, live executor identity, credentials, target service/environment, production approval, rollback authority, cost approval, cutover/decommission approval, or any missing identity from chat or prior conversations.

A fully qualified synthetic `execution_review_ready` Iteration 14 fixture may proceed only with a separate explicit synthetic rehearsal decision and complete explicit rehearsal envelope. It may compile and simulate one no-op execution attempt with exactly ten deterministic ordered per-step rehearsal receipts. Every receipt must prove evaluation without real external execution. Every real integration-plan step must remain disabled, and all production/cutover/decommission/publication flags must remain false.

Add one bounded rehearsal-only path through the existing canonical owner, such as `integration_execution_rehearsal_only=True`. Do not introduce a second orchestrator.

Prove deterministic rehearsal replay, exact Iteration 14 and upstream binding, stable classifications/reason codes, exactly ten no-op receipts for the synthetic review-ready proof, fail-closed stale/corrupted Iteration 14 input, fail-closed unsupported rehearsal versions, fail-closed changed policy/manifest/decision identity, proof that review-ready alone is insufficient without a separate rehearsal decision, proof that any real executable step fails closed before final artifact lock, targeted evaluation recovery, targeted one-receipt recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, zero reexecution of locked Iterations 1–14 work, and zero full-pipeline restart.

Do not implement or invoke a real production executor. Do not use production credentials, mutate the real/private Command Center, implement final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Any such requirement without explicit repository-authoritative zero-cost approval must fail closed.

Do not stop for routine engineering decisions. Continue through implementation, deterministic replay, injected-failure recovery, full regression testing, PR/CI validation, merge, and independent post-merge `main` verification.

Iteration 15 is complete only after three consecutive synthetic/shadow rehearsal-only runs independently satisfy the handoff exit gate. Merge only the exact candidate that passes the complete regression and Iteration 15 suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION15_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 15 evidence under `evidence/iteration15/`;
- authoritative Iteration 16 handoff;
- separate ready-to-paste Iteration 16 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, closure-document paths, and whether Iteration 16 is ready to begin.
