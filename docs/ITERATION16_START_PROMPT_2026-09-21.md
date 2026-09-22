# Ready-to-Paste Iteration 16 Start Prompt

**Activation status:** NOT READY until reconciled Iteration 15 repository closure reports `repository_closure_status=complete` and `iteration16_ready=true`.

@GitHub Proceed with Iteration 16 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 15 is completely closed and passing, and read:

- `docs/ITERATION16_HANDOFF_2026-09-21.md`
- `docs/ITERATION15_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration15/synthetic-shadow-production-integration-execution-rehearsal-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 16 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 15 evidence reports a pending closure package or `iteration16_ready=false`. Establish the starting baseline only from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–15 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, and the exact locked Iteration 15 `production-integration-execution-rehearsal` artifact with its exact `execution_rehearsal_id`, rehearsal policy/manifest identity, separate rehearsal-decision identity, deterministic execution-attempt identity, ordered no-op receipt identities, exact Iteration 14 execution-preflight binding, Iteration 13 admission, Iteration 12 ten-step plan, dry-run/rollback bindings, all transitive upstream identities, current blocked classification/reason codes, disabled real steps, and fixed non-production flags.

Implement Iteration 16 only: a deterministic, synthetic-only production-integration execution authorization-review gate from the exact locked Iteration 15 rehearsal artifact.

Build one versioned content-addressed `production-integration-execution-authorization-review` artifact, or the equivalent required by the handoff, that directly binds the exact Iteration 15 artifact digest and `execution_rehearsal_id`, its execution-attempt identity, rehearsal policy/manifest/decision identities, exact receipt inventory, the Iteration 14 execution preflight, Iteration 13 admission, Iteration 12 plan and ten-step graph, dry-run assertions, rollback boundaries, and all transitive upstream identities.

The current repository must remain `blocked` because its locked Iteration 15 rehearsal artifact is blocked. Do not infer authorization-review approval, production authority, executable steps, live executor identity, credentials, target service/environment, rollback authority, cost approval, cutover/decommission approval, or any missing identity from chat or prior conversations.

A fully qualified synthetic `rehearsal_complete` Iteration 15 fixture may be classified `authorization_review_ready` only with a separate explicit synthetic authorization-review decision and complete explicit review envelope. This is review readiness only: it must not grant production authority, enable a real step, use credentials, invoke a real executor, contact a real target, deploy, publish, cut over, or mutate any external surface. All production/cutover/decommission/publication/executor/credential authorization flags must remain false.

Add one bounded authorization-review-only path through the existing canonical owner, such as `integration_execution_authorization_review_only=True`. Do not introduce a second orchestrator.

Prove deterministic replay, exact Iteration 15 and upstream binding, stable classifications/reason codes, exact receipt-set validation, fail-closed stale/corrupted Iteration 15 input, fail-closed reordered/duplicated/corrupted/real-service receipt substitution, fail-closed unsupported review versions, fail-closed changed policy/manifest/decision identity, proof that rehearsal-complete alone is insufficient without a separate review decision, proof that any real executable step or authority flag fails closed, targeted evaluation recovery, targeted receipt-verification recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, zero reexecution of locked Iterations 1–15 work, and zero full-pipeline restart.

Do not implement or invoke a real production executor. Do not use production credentials, mutate the real/private Command Center, implement final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Any such requirement without explicit repository-authoritative zero-cost approval must fail closed.

Do not stop for routine engineering decisions. Continue through implementation, deterministic replay, injected-failure recovery, full regression testing, PR/CI validation, merge, and independent post-merge `main` verification.

Iteration 16 is complete only after three consecutive synthetic/shadow authorization-review-only runs independently satisfy the handoff exit gate. Merge only the exact candidate that passes the complete regression and Iteration 16 suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION16_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 16 evidence under `evidence/iteration16/`;
- authoritative Iteration 17 handoff;
- separate ready-to-paste Iteration 17 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, closure-document paths, and whether Iteration 17 is ready to begin.
