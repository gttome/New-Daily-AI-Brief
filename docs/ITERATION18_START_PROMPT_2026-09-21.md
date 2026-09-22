# Iteration 18 — Ready-to-Paste Start Prompt

> **ACTIVATION STATUS: PENDING ITERATION 17 CLOSURE RECONCILIATION.** Do not execute this prompt until current repository evidence reports `repository_closure_status=complete` and `iteration18_ready=true`.

@GitHub Proceed with Iteration 18 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 17 is completely closed and passing, and read:

- `docs/ITERATION18_HANDOFF_2026-09-21.md`
- `docs/ITERATION17_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration17/synthetic-shadow-production-integration-execution-authorization-decision-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 18 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 17 evidence reports a pending closure package or `iteration18_ready=false`. Establish the starting baseline only from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–17 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, and the exact locked Iteration 17 `production-integration-execution-authorization-decision` artifact with its exact `authorization_decision_id`, decision policy/manifest identity, separate authorization-decision identity, exact Iteration 16 authorization-review binding, exact provenance-validation identities, current classification/reason codes, disabled real steps, and fixed non-production flags.

Preserve the exact bound Iteration 16 authorization-review artifact digest and `authorization_review_id`, its review policy/manifest/review-decision identities and exact receipt-verification set; the exact bound Iteration 15 rehearsal artifact digest, `execution_rehearsal_id`, deterministic `execution_attempt_id`, rehearsal policy/manifest/decision identities, ordered no-op receipt set; the exact Iteration 14 execution preflight; Iteration 13 admission; Iteration 12 plan and ten-step graph; dry-run/rollback bindings; and all transitive Iterations 11/10/9 identities.

Implement Iteration 18 only: a deterministic, synthetic-only production-integration execution authorization-package gate from the exact locked Iteration 17 authorization-decision artifact.

Build one versioned content-addressed `production-integration-execution-authorization-package` artifact, or the equivalent required by the handoff, that directly binds the exact Iteration 17 artifact digest and `authorization_decision_id`, its policy/manifest/separate-decision identities, exact provenance-validation set, and every required transitive Iteration 16/15/14/13/12/11/10/9 identity.

The current repository must remain `blocked` because its locked Iteration 17 authorization-decision artifact is blocked. Do not infer an authorization package, production authority, executable steps, live executor identity, credentials, target service/environment, rollback authority, cost approval, cutover/decommission/publication approval, or any missing identity from chat or prior conversations.

A fully qualified synthetic `authorization_decision_ready` Iteration 17 fixture may be classified `authorization_package_ready` only with a separate explicit synthetic authorization-package record and complete explicit package envelope. This is package-boundary readiness only: it must not grant production authority, enable or execute a real step, use credentials, invoke a real executor, contact a real target, deploy, publish, cut over, decommission, or mutate any external surface. All production/cutover/decommission/publication/executor/credential/target/rollback authorization flags must remain false.

Add one bounded authorization-package-only path through the existing canonical owner, such as `integration_execution_authorization_package_only=True`. Do not introduce a second orchestrator.

Prove deterministic replay, exact Iteration 17 and upstream binding, stable classifications/reason codes, exact provenance-validation-set validation, fail-closed stale/corrupted Iteration 17 input, fail-closed reordered/duplicated/corrupted provenance substitution, fail-closed unsupported package versions, fail-closed changed Iteration 17 policy/manifest/separate-decision or Iteration 18 package identity, proof that `authorization_decision_ready` alone is insufficient without a separate authorization-package record, proof that any real executable step or authority flag fails closed, targeted package-evaluation recovery, targeted package provenance/validation recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, zero reexecution of locked Iterations 1–17 work, zero Iteration 17 artifact rebuild, and zero full-pipeline restart.

Do not implement or invoke a real production executor. Do not use or store production credentials, contact a real target, grant real execution authority, mutate the real/private Command Center, implement final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Any such requirement without explicit repository-authoritative zero-cost approval must fail closed.

Do not stop for routine engineering decisions. Continue through implementation, deterministic replay, injected-failure recovery, full regression testing, PR/CI validation, merge, and independent post-merge `main` verification.

Iteration 18 is complete only after three consecutive synthetic/shadow authorization-package-only runs independently satisfy the handoff exit gate. Merge only the exact candidate that passes the complete regression and Iteration 18 suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION18_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 18 evidence under `evidence/iteration18/`;
- authoritative Iteration 19 handoff;
- separate ready-to-paste Iteration 19 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, closure-document paths, and whether Iteration 19 is ready to begin.
