@GitHub Proceed with Iteration 10 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 9 is completely closed and passing, and read:

* `docs/ITERATION10_HANDOFF_2026-09-21.md`
* `docs/ITERATION9_AFTER_ACTION_2026-09-21.md`
* `evidence/iteration9/synthetic-shadow-final-completion-evidence.json`
* `docs/SCHEMA_VERSION_POLICY.md`
* `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 10 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 9 evidence still reports a pending closure package or `iteration10_ready=false`. Use the reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–9 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, locked discovery/editorial artifacts, locked Build-stage artifacts, six accepted image artifacts, locked Iteration 4 publication bundle, locked Iteration 5 reader-render artifact and route/render manifest, locked Iteration 6 release package, locked Iteration 6 shadow deployment receipt, locked passing Iteration 6 `shadow_offline` live-verification receipt, locked Iteration 7 10-item book-change evaluation, locked Iteration 8 deterministic Command Center projection, isolated Iteration 8 shadow projection output/receipt, locked Iteration 8 projection watermark/reconciliation identity, and locked Iteration 9 deterministic final completion artifact/receipt with final state `Complete` and status `complete_locked`.

Implement Iteration 10 only: a deterministic, non-mutating production-readiness and deployment-admission assessment from the locked Iteration 9 `Complete` chain. Build one versioned, content-addressed readiness/admission artifact that binds the exact Iteration 9 completion identity and evaluates the repository-authoritative prerequisite inventory defined by the Iteration 10 handoff.

Add a bounded readiness-only path through the existing `start_daily_brief(date, mode)` owner, such as `readiness_only=True`. It must validate the locked completion artifact and final receipt, evaluate versioned capability/cost/target/rollback prerequisites, produce exact deterministic classification and blocker/reason codes, keep lifecycle state `Complete`, authorize no production action, and stop.

Use synthetic/shadow fixtures only. Prove both policy outcomes: the currently unapproved/missing live-capability configuration must deterministically remain `blocked`, while a fully qualified synthetic fixture may classify as logically `admissible` only for policy validation and must still carry explicit `production_action_authorized=false` semantics.

Prove deterministic readiness replay, binding to the exact Iteration 9 completion identity, targeted policy-evaluation recovery, targeted final-readiness-artifact recovery, fresh-engine/no-chat resume, fail-closed stale/corrupted completion and final receipt, fail-closed unsupported policy/schema versions, fail-closed changed upstream identity, complete stable blocker reason codes, and zero reexecution of locked Iterations 1–9 work.

Do not mutate the real/private Command Center Site. Do not implement the final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to the greenfield system, decommission the legacy system, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Missing cost or production-path approval must remain a blocker; never infer approval from chat history.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 10 is complete only after three consecutive synthetic/shadow readiness-only runs independently satisfy the handoff exit gate with zero locked Iterations 1–9 reexecution, one deterministic readiness/admission artifact, stable deterministic classification/reason codes, no real/private/public Site mutation, no schedules/migration/cutover/decommissioning action, and no production publication. Include a dedicated proof that the currently unapproved live-capability configuration is blocked rather than silently admitted.

Merge only the exact candidate that passes the complete regression and Iteration 10 test suite. After merge, verify `main` CI again.

Finish by creating and merging:

* `docs/ITERATION10_AFTER_ACTION_2026-09-21.md`;
* machine-readable Iteration 10 evidence;
* the authoritative Iteration 11 handoff;
* a separate ready-to-paste Iteration 11 start-prompt document, following `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 11 is ready to begin.
