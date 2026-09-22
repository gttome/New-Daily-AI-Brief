@GitHub Proceed with Iteration 7 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 6 is completely closed and passing, and read:

* `docs/ITERATION7_HANDOFF_2026-09-21.md`
* `docs/ITERATION6_AFTER_ACTION_2026-09-21.md`
* `evidence/iteration6/synthetic-shadow-release-evidence.json`
* `docs/SCHEMA_VERSION_POLICY.md`
* `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 7 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 6 evidence still reports a pending closure package or `iteration7_ready=false`. Use the reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–6 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, locked discovery/editorial artifacts, locked Build-stage artifacts, six accepted image artifacts, locked Iteration 4 publication bundle, locked Iteration 5 reader-render artifact and route/render manifest, locked Iteration 6 release package, locked Iteration 6 shadow deployment receipt, and locked passing Iteration 6 `shadow_offline` live-verification receipt.

Implement Iteration 7 only: deterministic synthetic/shadow post-publication Generative AI Professional Series book-change evaluation of every included brief item, through the existing `LiveVerified → PostPublicationEvaluation` lifecycle. Evaluate exactly the six articles/stories, two verified videos, and two verified podcasts represented by the locked release chain. Persist explicit item-level dispositions so a true `0 proposals` result can never be confused with missing/incomplete evaluation.

Stop at `PostPublicationEvaluation` with a bounded status such as `post_publication_evaluation_locked`. Do not transition to `OperationsReconciled`, project to the Command Center, or create final completion.

Use synthetic/shadow fixtures/adapters first. Bind evaluation identity to the locked publication bundle, route manifest, release package, shadow deployment identity/receipt, and passing live-verification receipt. Prove deterministic replay, exact 10-item membership, correct proposal count/records, true-zero-versus-missing semantics, targeted one-item evaluation recovery, targeted final evaluation-artifact recovery, fresh-engine/no-chat resume, fail-closed stale/corrupted live verification, fail-closed incomplete/corrupted item evaluation, and zero reexecution of locked Iteration 1–6 work.

Do not deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, project to the Command Center, implement Command Center UI, create or modify production schedules, change subscriber delivery, migrate legacy content, cut over production, or decommission the legacy system. Do not modify or interrupt `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid evaluation API, paid deployment/hosting API, or other incremental paid production dependency. Keep every production evaluation/deployment adapter fail closed unless an approved zero-incremental-cost production path is separately authorized.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 7 is complete only after three consecutive synthetic/shadow evaluation-only runs independently satisfy the handoff exit gate with zero unrelated locked-stage reexecution, exactly 10 explicit item evaluations, one deterministic locked post-publication evaluation artifact, final state `PostPublicationEvaluation`, no `OperationsReconciled` transition, no Command Center projection, no final completion, and no public deployment/live-route mutation.

Merge only the exact candidate that passes the complete regression and Iteration 7 test suite. After merge, verify `main` CI again.

Finish by creating and merging:

* `docs/ITERATION7_AFTER_ACTION_2026-09-21.md`;
* machine-readable Iteration 7 evidence;
* the authoritative Iteration 8 handoff;
* a separate ready-to-paste Iteration 8 start-prompt document, following `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 8 is ready to begin.
