@GitHub Proceed with Iteration 9 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 8 is completely closed and passing, and read:

* `docs/ITERATION9_HANDOFF_2026-09-21.md`
* `docs/ITERATION8_AFTER_ACTION_2026-09-21.md`
* `evidence/iteration8/synthetic-shadow-operations-reconciliation-evidence.json`
* `docs/SCHEMA_VERSION_POLICY.md`
* `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 9 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 8 evidence still reports a pending closure package or `iteration9_ready=false`. Use the reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–8 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, locked discovery/editorial artifacts, locked Build-stage artifacts, six accepted image artifacts, locked Iteration 4 publication bundle, locked Iteration 5 reader-render artifact and route/render manifest, locked Iteration 6 release package, locked Iteration 6 shadow deployment receipt, locked passing Iteration 6 `shadow_offline` live-verification receipt, locked Iteration 7 10-item book-change evaluation, locked Iteration 8 deterministic Command Center projection, isolated shadow projection output/receipt, and locked Iteration 8 projection watermark/reconciliation identity.

Implement Iteration 9 only: deterministic synthetic/shadow final lifecycle completion and run closeout through the existing `OperationsReconciled → Complete` transition. Reuse the existing completion primitive and canonical orchestrator. Build one deterministic final completion artifact/event that binds the complete Iterations 1–8 canonical chain and explicitly identifies itself as synthetic/shadow validation, not production cutover.

Add a bounded completion-only path through `start_daily_brief(date, mode)`. It must validate the entire locked chain, validate the Iteration 8 shadow projection output/receipt and current projection watermark, build/reuse one content-addressed final completion record, transition exactly once to `Complete`, set a bounded final status such as `complete_locked`, and stop.

Use synthetic/shadow adapters only. Prove deterministic completion replay, complete transitive identity binding, explicit non-production completion scope, targeted completion-artifact recovery, targeted final-state/receipt recovery, fresh-engine/no-chat resume, fail-closed stale/corrupted verification/evaluation/projection/watermark/completion state, and zero reexecution of locked Iterations 1–8 work.

Do not mutate the real/private Command Center Site. Do not implement Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create or modify production schedules, change subscriber delivery, migrate legacy content, cut over production, decommission the legacy system, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. Keep every production/private-live path fail closed unless an approved zero-incremental-cost production path is separately authorized.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 9 is complete only after three consecutive synthetic/shadow completion-only runs independently satisfy the handoff exit gate with zero unrelated locked-stage reexecution, one deterministic final completion artifact/event, final state `Complete`, a bounded final status such as `complete_locked`, no real/private/public Site mutation, no schedules/migration/cutover/decommissioning action, and no production publication.

Merge only the exact candidate that passes the complete regression and Iteration 9 test suite. After merge, verify `main` CI again.

Finish by creating and merging:

* `docs/ITERATION9_AFTER_ACTION_2026-09-21.md`;
* machine-readable Iteration 9 evidence;
* the authoritative Iteration 10 handoff;
* a separate ready-to-paste Iteration 10 start-prompt document, following `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 10 is ready to begin.
