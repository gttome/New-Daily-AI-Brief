# New Daily AI Brief — Iteration 4 Handoff
## Image Completion & Deterministic Validation Bundle
### Prepared September 21, 2026

## Activation condition

Use this handoff only after Iteration 3 is merged to `main` and post-merge `Greenfield Contracts` CI passes.

Iteration 4 starts from the same greenfield control plane and the locked Iteration 3 Build-stage artifacts. It must not introduce another lifecycle owner, orchestrator, or workflow topology.

## Starting point

Iterations 1–3 provide:

- canonical `start_daily_brief(date, mode)`;
- durable lifecycle, lease/idempotency, content-addressed locks/digests, descendant invalidation, incidents/recovery receipts, completion primitives;
- deterministic six-story exact 2/2/2 edition with exactly one reusable Agent Skills story;
- exactly 2 verified videos and exactly 2 verified podcasts;
- canonical date-current Emerging AI Watchlist delta;
- centralized six-story Professional Series bridge decisions;
- targeted no-chat recovery with zero upstream editorial reexecution.

The authoritative Iteration 3 closure record is `docs/ITERATION3_AFTER_ACTION_2026-09-21.md`.

## Mission

Complete the remaining pre-release content work and deterministic validation contract **without public release or deployment**.

Iteration 4 is intentionally narrower than “publish the site.”

### A. Six story-specific image artifacts

Implement the real image contract behind the existing `images` artifact boundary while preserving the current state machine.

Required semantic result:

- exactly **6 accepted image records**;
- exactly one image bound to each locked edition story;
- no duplicate story binding;
- binary/content digest and provenance for each accepted image;
- durable per-story image state;
- bounded retry/regeneration/recovery;
- deterministic replay when the same accepted image inputs are reused;
- failure of one image repairs only that image boundary and does not rerun discovery, editorial, media, Watchlist, book bridges, or already accepted images.

Image acceptance requirements carried forward into the contract:

- story-specific professional textbook/editorial illustration;
- high detail and high information density;
- white background;
- 1200×630 target;
- WebP preferred; PNG acceptable;
- no sparse generic box-and-arrow fallback;
- no reused composition as a substitute for story specificity;
- no photo/people/decorative collage treatment;
- no clipped or overlapping text;
- accepted image must visually explain the mechanism in its story.

For synthetic tests, deterministic accepted-image fixtures may stand in for binaries. Any actual shadow image accepted during Iteration 4 must be visually inspected against the same contract.

Do **not** add a separately billed image API or other incremental paid production dependency. If no approved zero-incremental-cost autonomous production image path exists yet, keep the production image adapter fail-closed rather than silently degrading image quality.

### B. Deterministic validation/publication bundle

Extend the existing `Validating` stage only far enough to create and lock a **publication-ready validation bundle**, without releasing it.

The bundle must bind the exact locked identities for:

- edition;
- media;
- images;
- Watchlist;
- Professional Series bridges;
- rating contract.

Validation must fail closed if any required artifact is missing, stale, invalidated, wrong-date, schema-incompatible, or violates cardinality/invariant rules.

At minimum validate:

- 6 ordered stories with exact 2/2/2 allocation;
- exactly one reusable Agent Skills story;
- exactly 2 verified videos;
- exactly 2 verified podcasts;
- exactly 6 accepted story images;
- date-current Watchlist delta;
- exactly 6 book-bridge decisions;
- explicit no-bridge is valid;
- all artifact input digests match the currently locked upstream records;
- no stale edition-date reuse;
- deterministic bundle digest for identical locked inputs.

### C. Validation-only execution boundary

Add a bounded validation-only path that:

1. starts through the canonical `start_daily_brief(date, mode)` entry point;
2. reuses already locked Iteration 1–3 artifacts;
3. completes image work;
4. performs deterministic validation;
5. locks the validation/publication bundle;
6. stops before any release, deployment, public rendering, live verification, Command Center projection, schedule, migration, or cutover action.

Do not bypass the existing lifecycle to achieve this.

## Recovery requirements

Injected failures must prove targeted recovery for at least:

- one image boundary after other images are already accepted;
- one validation boundary after all Build artifacts are locked.

A fresh engine instance must resume without chat/session context.

Required anti-rework result:

- zero discovery reexecution;
- zero editorial reexecution;
- zero media reexecution;
- zero unrelated Watchlist reexecution;
- zero unrelated bridge reexecution;
- zero already accepted image rework;
- zero full-pipeline restart.

## Telemetry

Persist bounded Iteration 4 telemetry for:

- image attempts/retries/rejections/acceptances;
- accepted-image reuse;
- per-image recovery;
- validation checks and failures by invariant;
- validation bundle reuse;
- elapsed time;
- anti-rework counters.

Volatile telemetry must remain outside semantic content identity.

## Explicit non-scope

Iteration 4 must **not** implement:

- public Site page rendering;
- homepage/latest/story/archive/feed output;
- Command Center UI or projection;
- GitHub Pages or other deployment;
- live-route verification;
- production schedules;
- subscriber delivery changes;
- legacy-content migration;
- production cutover;
- legacy decommissioning.

Do not modify or interrupt `gttome/Daily-AI-Brief`.

## Required proof

At minimum prove:

1. exactly six accepted image records, one per story;
2. bounded retry/rejection behavior;
3. targeted one-image failure recovery;
4. no-chat resume inside pre-release lifecycle;
5. deterministic image artifact replay for identical accepted inputs;
6. fail-closed validation on a missing/invalid required artifact;
7. exact cardinality/invariant validation for edition/media/images/Watchlist/bridges;
8. deterministic publication/validation bundle replay;
9. zero reexecution of locked Iteration 1–3 work;
10. no release, deployment, public rendering, schedules, or cutover.

## Exit gate

Iteration 4 is complete only after **three consecutive synthetic/shadow validation-only runs**, each beginning from valid locked Iteration 3 artifacts, independently produce without manual intervention:

- 6 accepted story images;
- all Iteration 1–3 locked artifacts reused correctly;
- a passing deterministic validation result;
- one locked publication/validation bundle;
- identical bundle digest when identical locked inputs are replayed;
- zero unrelated locked-stage reexecution;
- no public rendering;
- no release;
- no deployment;
- no production publication.

Merge only the exact candidate that passes the complete regression + Iteration 4 suite. After merge, verify `main` CI again.

## Required closure records

Finish Iteration 4 by creating:

- `docs/ITERATION4_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 4 evidence;
- the authoritative next-iteration handoff based on the validated state at that time.

## Launch prompt

```text
@GitHub Proceed with Iteration 4 of the New Daily AI Brief greenfield implementation using docs/ITERATION4_HANDOFF_2026-09-21.md in gttome/New-Daily-AI-Brief.

Start from the merged Iteration 1–3 control plane and locked artifacts. Preserve the existing lifecycle, canonical start_daily_brief(date, mode) entry point, lease/idempotency, content-addressed locks/digests, descendant invalidation, incidents/recovery receipts, and anti-rework guarantees.

Implement Iteration 4 only: exactly six accepted story-specific image artifacts with bounded per-image recovery, then deterministic validation/publication-bundle assembly that binds edition, media, images, Watchlist, Professional Series bridges, and rating contract. Add a validation-only stop before release.

Use synthetic/shadow fixtures first. Do not add a separately billed API or incremental paid production dependency. If a zero-incremental-cost autonomous production image path is not yet approved and proven, keep production image generation fail-closed.

Do not implement public Site rendering, archive/feed output, Command Center UI, deployment/live verification, production schedules, migration, cutover, or legacy decommissioning. Do not modify gttome/Daily-AI-Brief.

Continue through implementation, targeted failure recovery, deterministic replay, full regression testing, PR/CI validation, merge, post-merge main CI verification, after-action evidence, and the next authoritative handoff.
```
