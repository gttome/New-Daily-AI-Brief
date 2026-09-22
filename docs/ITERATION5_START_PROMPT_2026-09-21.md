# New Daily AI Brief — Iteration 5 Start Prompt
### Prepared September 21, 2026

Copy the complete prompt below into a **new ChatGPT chat** and invoke GitHub.

```text
@GitHub Proceed with Iteration 5 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 4 is completely closed and passing, and read:

- `docs/ITERATION5_HANDOFF_2026-09-21.md`
- `docs/ITERATION4_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration4/synthetic-validation-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 5 handoff is the controlling implementation specification.

Start from the merged Iteration 1–4 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, locked discovery/editorial artifacts, locked Build-stage artifacts, six accepted image artifacts, and locked Iteration 4 validation/publication bundle.

Implement Iteration 5 only: deterministic shadow/static reader-surface rendering from the passing locked Iteration 4 publication bundle plus one deterministic route/render manifest. Preserve exact story order and exact media, Watchlist, Professional Series bridge, image, and five-star rating-contract semantics. Include current/latest/dated/story surfaces plus deterministic archive/feed representation as specified by the handoff.

Use synthetic/shadow fixtures/templates first. Prove targeted one-route recovery, archive/feed recovery, render-manifest validation recovery, no-chat resume, deterministic replay, fail-closed rendering/validation, exact parity checks, and zero reexecution of locked Iteration 1–4 work.

Do not deploy, change live/public URLs, perform live-route verification, project to the Command Center, implement Command Center UI, create or modify production schedules, change subscriber delivery, migrate legacy content, cut over production, or decommission the legacy system. Do not modify or interrupt `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid rendering API, or other incremental paid production dependency. If a production rendering/hosting dependency is not approved at zero incremental cost, keep that production adapter fail closed.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 5 is complete only after three consecutive synthetic/shadow render-only runs independently satisfy the handoff exit gate with zero unrelated locked-stage reexecution and no release/deployment/live-route mutation.

Merge only the exact candidate that passes the complete regression and Iteration 5 test suite. After merge, verify `main` CI again.

Finish by creating and merging:
- `docs/ITERATION5_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 5 evidence;
- the authoritative Iteration 6 handoff;
- a separate ready-to-paste Iteration 6 start-prompt document, following `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 6 is ready to begin.
```
