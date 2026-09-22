# New Daily AI Brief — Iteration 4 Start Prompt
### Prepared September 21, 2026

Copy the complete prompt below into a **new ChatGPT chat** and invoke GitHub.

```text
@GitHub Proceed with Iteration 4 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 3 remains completely merged and passing, and read:

- `docs/ITERATION4_HANDOFF_2026-09-21.md`
- `docs/ITERATION3_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration3/synthetic-build-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 4 handoff is the controlling implementation specification.

Start from the merged Iteration 1–3 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, locked discovery/editorial artifacts, and locked Iteration 3 Build-stage artifacts.

Implement Iteration 4 only:

1. exactly six accepted story-specific image artifacts, one per locked story, with bounded per-image retry/recovery and deterministic reuse;
2. deterministic validation/publication-bundle assembly binding edition, media, images, Watchlist, Professional Series bridges, and rating contract;
3. a validation-only stop before release.

Use synthetic/shadow fixtures first. Prove targeted one-image failure recovery, validation-boundary recovery, no-chat resume, deterministic replay, fail-closed validation, exact cardinality/invariant checks, and zero reexecution of locked Iteration 1–3 work.

Image quality requirements are contractual:
- professional textbook/editorial quality;
- story-specific and mechanism-explanatory;
- high detail and information density;
- white background;
- 1200×630 target;
- WebP preferred; PNG acceptable;
- no sparse generic box-and-arrow fallback;
- no reused composition as a substitute for story specificity;
- no photos, people, decorative collage treatment, clipped text, or overlapping text.

Do not add a separately billed OpenAI API, paid image API, or other incremental paid production dependency. If a zero-incremental-cost autonomous production image path is not approved and proven, keep production image generation fail-closed rather than degrading image quality.

Do not implement public Site rendering, homepage/latest/story/archive/feed output, Command Center UI/projection, deployment/live verification, production schedules, subscriber-delivery changes, legacy-content migration, production cutover, or legacy decommissioning. Do not modify or interrupt `gttome/Daily-AI-Brief`.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 4 is complete only after three consecutive synthetic/shadow validation-only runs independently produce without manual intervention:
- exactly 6 accepted story images;
- correct reuse of all locked Iteration 1–3 artifacts;
- a passing deterministic validation result;
- one locked validation/publication bundle;
- identical bundle digest for identical locked inputs;
- zero unrelated locked-stage reexecution;
- no release, public rendering, deployment, schedule, or production publication.

Merge only the exact candidate that passes the complete regression and Iteration 4 test suite. After merge, verify `main` CI again.

Finish by creating and merging:
- `docs/ITERATION4_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 4 evidence;
- the authoritative Iteration 5 handoff;
- a separate ready-to-paste Iteration 5 start-prompt document, following `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 5 is ready to begin.
```
