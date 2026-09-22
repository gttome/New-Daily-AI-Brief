@GitHub Proceed with Iteration 8 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 7 is completely closed and passing, and read:

* `docs/ITERATION8_HANDOFF_2026-09-21.md`
* `docs/ITERATION7_AFTER_ACTION_2026-09-21.md`
* `evidence/iteration7/synthetic-shadow-evaluation-evidence.json`
* `docs/SCHEMA_VERSION_POLICY.md`
* `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 8 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 7 evidence still reports a pending closure package or `iteration8_ready=false`. Use the reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–7 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, locked discovery/editorial artifacts, locked Build-stage artifacts, six accepted image artifacts, locked Iteration 4 publication bundle, locked Iteration 5 reader-render artifact and route/render manifest, locked Iteration 6 release package, locked Iteration 6 shadow deployment receipt, locked passing Iteration 6 `shadow_offline` live-verification receipt, and locked Iteration 7 book-change evaluation with exactly 10 explicit item evaluations.

Implement Iteration 8 only: deterministic synthetic/shadow operations reconciliation and Command Center projection modeling through the existing `PostPublicationEvaluation → OperationsReconciled` lifecycle. Build a deterministic projection payload from the complete locked canonical chain, materialize it only to an isolated fixture/filesystem shadow target, and lock a projection watermark/reconciliation artifact that makes current/stale/mismatched state detectable.

Stop at `OperationsReconciled` with a bounded status such as `operations_reconciled_locked`. Do not transition to `Complete` or create final completion.

Use synthetic/shadow adapters first. The projection must represent and bind the exact six stories, four verified media items, Watchlist state, six bridge decisions, six accepted image bindings, rating contract, publication/render/release chain, passing live-verification identity, and Iteration 7 10-item evaluation/proposal result. Prove deterministic replay, projection identity binding, freshness/currentness semantics, targeted shadow-projection recovery, targeted final watermark/reconciliation recovery, fresh-engine/no-chat resume, fail-closed stale/corrupted verification/evaluation/projection state, and zero reexecution of locked Iteration 1–7 work.

Do not mutate the real/private Command Center Site in this iteration. Do not implement Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create or modify production schedules, change subscriber delivery, migrate legacy content, cut over production, decommission the legacy system, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid projection/storage API, paid deployment/hosting API, or other incremental paid production dependency. Keep every private-live/production projection, evaluation, and deployment adapter fail closed unless an approved zero-incremental-cost production path is separately authorized.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 8 is complete only after three consecutive synthetic/shadow reconcile-only runs independently satisfy the handoff exit gate with zero unrelated locked-stage reexecution, one deterministic projection payload, one shadow projection receipt/output, one locked projection watermark/reconciliation artifact, final state `OperationsReconciled`, no `Complete` transition, no final completion artifact, and no real/private/public Site mutation.

Merge only the exact candidate that passes the complete regression and Iteration 8 test suite. After merge, verify `main` CI again.

Finish by creating and merging:

* `docs/ITERATION8_AFTER_ACTION_2026-09-21.md`;
* machine-readable Iteration 8 evidence;
* the authoritative Iteration 9 handoff;
* a separate ready-to-paste Iteration 9 start-prompt document, following `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 9 is ready to begin.
