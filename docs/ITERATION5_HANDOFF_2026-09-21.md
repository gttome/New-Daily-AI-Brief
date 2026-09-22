# New Daily AI Brief — Iteration 5 Handoff
## Deterministic Reader-Surface Rendering
### Prepared September 21, 2026

## Activation condition

Iteration 5 may begin only after the complete Iteration 4 closure package is present on verified `main`.

The validated Iteration 4 implementation baseline is:

- implementation merge: `1ea8975a446fd12580a065b054bc461b372e9e32`;
- post-merge `Greenfield Contracts` run: **35674251119**;
- complete regression suite: **43/43 PASS**.

Before changing anything, verify current `main` and read:

- `docs/ITERATION4_AFTER_ACTION_2026-09-21.md`;
- `evidence/iteration4/synthetic-validation-evidence.json`;
- `docs/SCHEMA_VERSION_POLICY.md`;
- `docs/ITERATION_START_PACKAGE_STANDARD.md`.

The current repository records, not chat history or a manually remembered SHA, are authoritative.

## Starting point

Iterations 1–4 provide one greenfield control plane and a locked, validated pre-release bundle:

- canonical `start_daily_brief(date, mode)`;
- durable lifecycle, lease/idempotency, content-addressed locks/digests, descendant invalidation, incidents/recovery receipts, and completion primitives;
- deterministic exact 2/2/2 six-story edition with exactly one reusable Agent Skills story;
- exactly 2 verified videos and exactly 2 verified podcasts;
- date-current Watchlist delta;
- exactly 6 centralized Professional Series bridge decisions;
- exactly 6 accepted story-specific image records;
- `five-star-v1` rating contract;
- deterministic validation/publication bundle binding all required pre-release inputs;
- validation-only stop before release;
- targeted no-chat recovery with zero unrelated locked-stage reexecution.

The locked Iteration 4 validation/publication bundle is immutable upstream input for Iteration 5.

## Mission

Implement the next bounded slice only: **deterministic reader-surface rendering from a passing locked Iteration 4 validation/publication bundle**.

Iteration 5 creates shadow/static render artifacts and a deterministic route manifest. It does **not** deploy them or change a live route.

Do not introduce another lifecycle owner or bypass `start_daily_brief(date, mode)`.

## A. Reader-render artifact

Extend the existing pre-release lifecycle with a content-addressed reader-render artifact derived only from the locked validation/publication bundle and versioned rendering contracts/templates.

At minimum, the shadow/static render must deterministically represent:

- the homepage/current-edition story list in the locked presentation order;
- the latest/current edition reader surface;
- a dated edition surface;
- six permanent story surfaces, one for each locked story;
- the edition's verified video and podcast content in deterministic order;
- Watchlist summary state, including current-day new/updated/carried-forward information;
- Professional Series bridge output exactly as decided upstream, including explicit no-bridge behavior;
- five-star rating/share contract hooks without inventing stored ratings;
- archive metadata needed to add the edition without rewriting historical semantic content;
- feed/RSS representation for the edition.

Render output must never reorder, silently omit, or editorially reinterpret the locked bundle.

## B. Deterministic route manifest

Create one locked route/render manifest that binds:

- validation/publication-bundle digest;
- rendering-contract/template version;
- every required route/output identity;
- content digest for every rendered output;
- archive/feed membership;
- accessibility/structural validation result;
- `release_authorized=false`.

Identical locked bundle + identical rendering-contract/template version must reproduce identical semantic render and manifest digests. Volatile timestamps, filesystem paths, and elapsed time must not affect semantic identity.

## C. Render validation

Fail closed before any release if:

- the Iteration 4 bundle is missing, invalidated, wrong-date, schema-incompatible, or not passing;
- any required route/output is missing;
- story count/order differs from the locked six-story edition;
- image/story binding differs from the locked bundle;
- media counts/order differ from the locked media artifact;
- Watchlist summary does not match the locked delta;
- a bridge decision is changed or fabricated;
- rating contract differs from `five-star-v1`;
- archive/feed representation is inconsistent with the current edition;
- required accessibility/structural checks fail;
- a rendered output digest does not match the route manifest.

## D. Validation-only / render-only boundary

Add a bounded render-only execution path through the canonical entry point that:

1. reuses all locked Iteration 1–4 artifacts;
2. validates the locked Iteration 4 publication bundle;
3. creates/reuses only required reader-render outputs;
4. validates and locks the route/render manifest;
5. stops before `Releasing`.

Do not bypass the existing state machine. If a new content-addressed rendering artifact must be added to the dependency graph, it must remain a descendant of the locked publication bundle and must invalidate only its descendants.

## Recovery requirements

Inject failures proving targeted recovery for at least:

- one individual story-route render after other routes are already locked/reusable;
- one archive/feed render boundary;
- one final render-manifest validation boundary.

A fresh engine instance must resume without chat/session context.

Required anti-rework result:

- zero discovery reexecution;
- zero editorial reexecution;
- zero media reexecution;
- zero Watchlist reexecution;
- zero bridge reexecution;
- zero accepted-image rework;
- zero publication-bundle rebuild when its inputs are unchanged;
- zero already completed unrelated route re-render;
- zero full-pipeline restart.

## Telemetry

Persist bounded Iteration 5 telemetry for:

- route render attempts/retries/rejections/completions;
- per-route cache reuse;
- archive/feed render work;
- render-validation checks/failures by invariant;
- render-manifest reuse;
- elapsed time;
- anti-rework counters.

Volatile telemetry must remain outside semantic content identity.

## Explicit non-scope

Iteration 5 must **not**:

- deploy to GitHub Pages or any other live host;
- change public/live URLs;
- perform live-route verification;
- project to the private Command Center;
- implement Command Center UI;
- create or modify production schedules;
- change subscriber delivery;
- migrate legacy historical content;
- cut over production;
- decommission the legacy system;
- modify or interrupt `gttome/Daily-AI-Brief`;
- add a separately billed OpenAI API, paid rendering API, or incremental paid production dependency.

If a production rendering/hosting dependency would create incremental cost, keep that production adapter fail closed until separately approved.

## Required proof

At minimum prove:

1. deterministic render replay for identical locked inputs;
2. exact six-story order parity across current/latest/dated/story surfaces;
3. media parity with exactly 2 videos and 2 podcasts;
4. exact Watchlist summary parity;
5. exact Professional Series bridge parity including no-bridge;
6. five-star contract preserved without fabricated rating data;
7. archive/feed membership parity;
8. route-manifest completeness and digest verification;
9. fail-closed behavior for missing/stale/corrupted locked bundle input;
10. targeted one-route recovery;
11. targeted archive/feed recovery;
12. render-manifest validation recovery;
13. fresh-engine/no-chat resume;
14. zero reexecution of locked Iteration 1–4 work;
15. no release, deployment, live verification, schedules, migration, or cutover.

## Exit gate

Iteration 5 is complete only after **three consecutive synthetic/shadow render-only runs**, each beginning from a valid locked Iteration 4 publication bundle, independently produce without manual intervention:

- one complete deterministic reader-render set;
- one complete locked route/render manifest;
- exact six-story order parity;
- exact media, Watchlist, bridge, image, and rating-contract parity;
- archive/feed consistency;
- passing structural/accessibility/render validation;
- identical semantic render/manifest digests for identical locked inputs;
- zero unrelated locked-stage reexecution;
- no `Releasing` transition;
- no deployment;
- no live-route mutation;
- no production publication.

Merge only the exact candidate that passes the complete regression + Iteration 5 suite. After merge, verify `main` CI again.

## Required closure records

Iteration 5 must follow `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Finish by creating and merging all four required closure artifacts:

- `docs/ITERATION5_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 5 evidence under `evidence/iteration5/`;
- authoritative `docs/ITERATION6_HANDOFF_2026-09-21.md`;
- standalone ready-to-paste `docs/ITERATION6_START_PROMPT_2026-09-21.md`.

Do not report Iteration 6 as ready until all four artifacts are present on verified `main`.
