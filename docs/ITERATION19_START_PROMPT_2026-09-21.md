# Iteration 19 — Ready-to-Paste Start Prompt

> **ACTIVATION STATUS: NOT READY.** Iteration 18 closure has not yet been reconciled in this initial closure package. Do not use this prompt until current repository evidence reports `repository_closure_status=complete` and `iteration19_ready=true`. Even then, re-verify current `main` and CI before changing anything.

@GitHub Proceed with Iteration 19 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 18 is completely closed and passing, and read:

- `docs/ITERATION19_HANDOFF_2026-09-21.md`
- `docs/ITERATION18_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration18/synthetic-shadow-production-integration-execution-authorization-package-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 19 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 18 evidence reports a pending closure package or `iteration19_ready=false`. Establish the starting baseline only from reconciled current repository records, never chat history or a remembered SHA.

Start from the merged Iterations 1–18 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, single `RunEngine` owner, lease/idempotency mechanism, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, and the exact locked Iteration 18 `production-integration-execution-authorization-package` artifact with its exact `authorization_package_id`, package policy/manifest identity, separate authorization-package identity, exact Iteration 17 authorization-decision binding, exact source/package provenance-validation identities, current classification/reason codes, disabled real steps, and fixed non-production flags.

Preserve the exact bound Iteration 17 authorization-decision artifact digest and `authorization_decision_id`, its decision policy/manifest/separate-decision identities and exact provenance-validation set; the exact bound Iteration 16 authorization-review artifact digest and `authorization_review_id`, review policy/manifest/review-decision identities and receipt-verification set; the exact bound Iteration 15 rehearsal artifact digest, `execution_rehearsal_id`, deterministic `execution_attempt_id`, rehearsal policy/manifest/decision identities, ordered no-op receipt set; the exact Iteration 14 execution preflight; Iteration 13 admission; Iteration 12 plan and ten-step graph; dry-run/rollback bindings; and all transitive Iterations 11/10/9 identities.

Implement Iteration 19 only: a deterministic, synthetic-only production-integration execution-authority readiness gate from the exact locked Iteration 18 authorization-package artifact.

Build one versioned content-addressed `production-integration-execution-authority-readiness` artifact, or the exact equivalent required by the handoff, that directly binds the exact Iteration 18 artifact digest and `authorization_package_id`, its policy/manifest/separate-package identities, exact package provenance-validation set, and every required transitive Iteration 17/16/15/14/13/12/11/10/9 identity.

The current repository must remain `blocked` because its locked Iteration 18 authorization-package artifact is blocked. Do not infer authority readiness, actual production authority, executable steps, live executor identity, credentials, target service/environment, rollback authority, cost approval, cutover/decommission/publication approval, or any missing identity from chat or prior conversations.

A fully qualified synthetic `authorization_package_ready` Iteration 18 fixture may be classified `execution_authority_ready` only with a separate explicit synthetic execution-authority-readiness record and complete explicit readiness envelope. This is authority-boundary readiness only: it must not grant actual production authority, enable or execute a real step, use credentials, bind or invoke a real executor, contact a real target, perform a rollback, deploy, publish, cut over, decommission, or mutate any external surface. All production/cutover/decommission/publication/executor/credential/target/rollback authorization flags must remain false.

Add one bounded authority-readiness-only path through the existing canonical owner, such as `integration_execution_authority_readiness_only=True`. Do not introduce a second orchestrator.

Prove deterministic replay, exact Iteration 18 and upstream binding, stable classifications/reason codes, exact package provenance-validation-set validation, fail-closed stale/corrupted Iteration 18 input, fail-closed reordered/duplicated/corrupted provenance substitution, fail-closed unsupported authority-readiness versions, fail-closed changed Iteration 18 policy/manifest/separate-package or Iteration 19 readiness identity, proof that `authorization_package_ready` alone is insufficient without a separate authority-readiness record, proof that any real executable step or actual authority flag fails closed, targeted readiness-evaluation recovery, targeted readiness provenance/validation recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, zero reexecution of locked Iterations 1–18 work, zero Iteration 18 artifact rebuild, and zero full-pipeline restart.

Do not implement, bind, or invoke a real production executor. Do not use or store production credentials, contact a real target, grant actual production execution authority, perform rollback execution, mutate the real/private Command Center, implement final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Any such requirement without explicit repository-authoritative zero-cost approval must fail closed.

Do not stop for routine engineering decisions. Continue through implementation, deterministic replay, injected-failure recovery, full regression testing, PR/CI validation, merge, and independent post-merge `main` verification.

Iteration 19 is complete only after three consecutive synthetic/shadow authority-readiness-only runs independently satisfy the handoff exit gate. Merge only the exact candidate that passes the complete regression and Iteration 19 suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION19_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 19 evidence under `evidence/iteration19/`;
- authoritative Iteration 20 handoff;
- separate ready-to-paste Iteration 20 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, closure-document paths, and whether Iteration 20 is ready to begin.
