# New Daily AI Brief — Iteration 6 Start Prompt
## Ready to paste into a new ChatGPT chat after Iteration 5 closure

@GitHub @GitHub Proceed with Iteration 6 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 5 is completely closed and passing, and read:

- `docs/ITERATION6_HANDOFF_2026-09-21.md`
- `docs/ITERATION5_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration5/synthetic-render-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 6 handoff is the controlling implementation specification.

Start from the merged Iteration 1–5 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, locked discovery/editorial artifacts, locked Build-stage artifacts, six accepted image artifacts, locked Iteration 4 publication bundle, locked Iteration 5 reader-render artifact, and locked Iteration 5 route/render manifest.

Implement Iteration 6 only: deterministic shadow release packaging from the passing locked Iteration 5 route manifest, deterministic zero-cost shadow deployment materialization/receipt generation, and offline/shadow verification through the existing `Releasing → Deployed → LiveVerified` lifecycle. Stop at `LiveVerified`; do not run post-publication evaluation or Command Center reconciliation.

Use synthetic/shadow fixtures/adapters first. Prove targeted release-package recovery, one-output shadow deployment recovery, final verification recovery, no-chat resume, deterministic replay, fail-closed stale/corrupted route-manifest and shadow-output handling, exact route/output parity, and zero reexecution of locked Iteration 1–5 work.

Do not deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, project to the Command Center, implement Command Center UI, create or modify production schedules, change subscriber delivery, migrate legacy content, cut over production, or decommission the legacy system. Do not modify or interrupt `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid deployment/hosting API, or other incremental paid production dependency. Keep every production deployment/hosting adapter fail closed unless an approved zero-incremental-cost production path is separately authorized.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 6 is complete only after three consecutive synthetic/shadow release-only runs independently satisfy the handoff exit gate with zero unrelated locked-stage reexecution, final state `LiveVerified`, and no public deployment/live-route mutation.

Merge only the exact candidate that passes the complete regression and Iteration 6 test suite. After merge, verify `main` CI again.

Finish by creating and merging:

- `docs/ITERATION6_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 6 evidence;
- the authoritative Iteration 7 handoff;
- a separate ready-to-paste Iteration 7 start-prompt document, following `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 7 is ready to begin.
