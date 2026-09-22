# Iteration 17 — Ready-to-Paste Start Prompt

@GitHub Proceed with Iteration 17 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 16 is completely closed and passing, and read:

- `docs/ITERATION17_HANDOFF_2026-09-21.md`
- `docs/ITERATION16_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration16/synthetic-shadow-production-integration-execution-authorization-review-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 17 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 16 evidence reports a pending closure package or `iteration17_ready=false`. Establish the starting baseline only from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–16 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, and the exact locked Iteration 16 `production-integration-execution-authorization-review` artifact with its exact `authorization_review_id`, review policy/manifest identity, separate review-decision identity, exact Iteration 15 rehearsal binding, exact receipt-verification identities, current classification/reason codes, disabled real steps, and fixed non-production flags.

Preserve the exact bound Iteration 15 rehearsal artifact digest and `execution_rehearsal_id`, deterministic execution-attempt identity, rehearsal policy/manifest/decision identities, ordered no-op receipt set, the exact Iteration 14 execution preflight, Iteration 13 admission, Iteration 12 plan and ten-step graph, dry-run/rollback bindings, and all transitive Iterations 11/10/9 identities.

Implement Iteration 17 only: a deterministic, synthetic-only production-integration execution authorization-decision gate from the exact locked Iteration 16 authorization-review artifact.

Build one versioned content-addressed `production-integration-execution-authorization-decision` artifact, or the equivalent required by the handoff, that directly binds the exact Iteration 16 artifact digest and `authorization_review_id`, its policy/manifest/review-decision identities, exact receipt-verification set, and every transitive Iteration 15/14/13/12/11/10/9 identity required by the handoff.

The current repository must remain `blocked` because its locked Iteration 16 authorization-review artifact is blocked. Do not infer an authorization decision, production authority, executable steps, live executor identity, credentials, target service/environment, rollback authority, cost approval, cutover/decommission/publication approval, or any missing identity from chat or prior conversations.

A fully qualified synthetic `authorization_review_ready` Iteration 16 fixture may be classified `authorization_decision_ready` only with a separate explicit synthetic authorization-decision record and complete explicit decision envelope. This is decision-boundary readiness only: it must not grant production authority, enable a real step, use credentials, invoke a real executor, contact a real target, deploy, publish, cut over, decommission, or mutate any external surface. All production/cutover/decommission/publication/executor/credential/target/rollback authorization flags must remain false.

Add one bounded authorization-decision-only path through the existing canonical owner, such as `integration_execution_authorization_decision_only=True`. Do not introduce a second orchestrator.

Prove deterministic replay, exact Iteration 16 and upstream binding, stable classifications/reason codes, exact receipt-verification-set validation, fail-closed stale/corrupted Iteration 16 input, fail-closed reordered/duplicated/corrupted verification substitution, fail-closed unsupported decision versions, fail-closed changed review policy/manifest/review-decision or authorization-decision identity, proof that `authorization_review_ready` alone is insufficient without a separate authorization-decision record, proof that any real executable step or authority flag fails closed, targeted evaluation recovery, targeted provenance/verification recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, zero reexecution of locked Iterations 1–16 work, and zero full-pipeline restart.

Do not implement or invoke a real production executor. Do not use production credentials, contact a real target, mutate the real/private Command Center, implement final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Any such requirement without explicit repository-authoritative zero-cost approval must fail closed.

Do not stop for routine engineering decisions. Continue through implementation, deterministic replay, injected-failure recovery, full regression testing, PR/CI validation, merge, and independent post-merge `main` verification.

Iteration 17 is complete only after three consecutive synthetic/shadow authorization-decision-only runs independently satisfy the handoff exit gate. Merge only the exact candidate that passes the complete regression and Iteration 17 suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION17_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 17 evidence under `evidence/iteration17/`;
- authoritative Iteration 18 handoff;
- separate ready-to-paste Iteration 18 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, closure-document paths, and whether Iteration 18 is ready to begin.
