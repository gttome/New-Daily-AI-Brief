# New Daily AI Brief — Iteration 6 Handoff
## Deterministic Shadow Release & Offline Verification
### Prepared September 21, 2026

## Activation condition

Iteration 6 is activated only after Iteration 5 operational closure is complete under `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Before changing anything, verify current `main` and read:

- `docs/ITERATION5_AFTER_ACTION_2026-09-21.md`;
- `evidence/iteration5/synthetic-render-evidence.json`;
- `docs/SCHEMA_VERSION_POLICY.md`;
- `docs/ITERATION_START_PACKAGE_STANDARD.md`.

The current repository records, not chat history or a manually remembered SHA, are authoritative.

## Validated implementation baseline

The Iteration 5 implementation was merged as:

`45e19aef1aff2ff371f7b572b37be36a8df1f0b3`

Its post-merge `Greenfield Contracts` run **35676287692** passed the complete **54/54** regression suite.

The closure package must also be present and green on current `main` before Iteration 6 begins.

## Starting point

Iterations 1–5 provide one recoverable greenfield control plane with:

- canonical `start_daily_brief(date, mode)`;
- durable lifecycle/state machine and lease/idempotency;
- content-addressed locks/digests and descendant-only invalidation;
- incident/recovery receipts and no-chat resume;
- deterministic exact 2/2/2 six-story edition with exactly one reusable Agent Skills story;
- exactly two verified videos and two verified podcasts;
- date-current Watchlist delta;
- exactly six Professional Series bridge decisions;
- exactly six accepted story images;
- `five-star-v1` rating contract;
- a passing locked Iteration 4 publication bundle;
- a locked Iteration 5 reader-render artifact;
- a locked Iteration 5 route/render manifest covering current/latest/dated/six story/archive/feed outputs;
- deterministic render replay and targeted route recovery;
- no production deployment or live-route mutation.

The locked Iteration 5 route manifest is immutable upstream input for Iteration 6.

## Mission

Implement the next bounded slice only: **deterministic shadow release packaging, shadow deployment-receipt generation, and offline/shadow live verification from the passing locked Iteration 5 route manifest**.

Iteration 6 may exercise the existing:

`Validating → Releasing → Deployed → LiveVerified`

lifecycle in **synthetic/shadow mode only**.

It must not publish to or mutate any public/live URL.

Do not introduce another lifecycle owner or bypass `start_daily_brief(date, mode)`.

## A. Deterministic release package

Create one content-addressed release-package artifact derived only from:

- the locked Iteration 5 route manifest;
- the locked reader-render outputs referenced by it;
- a versioned release-package contract.

The release package must deterministically bind:

- edition date;
- route-manifest digest;
- every output route and output digest;
- archive/feed membership;
- release-package contract version;
- `production_authorized=false`;
- `shadow_only=true`.

Volatile timestamps, local paths, and elapsed time must not affect semantic identity.

## B. Zero-cost shadow deployment adapter

Implement a deterministic synthetic/shadow deployment adapter that materializes the release package only into an isolated test/shadow state root or equivalent non-public fixture location.

Requirements:

- no GitHub Pages deployment;
- no public ChatGPT Site mutation;
- no DNS/URL mutation;
- no external paid hosting/rendering service;
- no production secret or credential requirement;
- deterministic deployment identity derived from the release package;
- deployment receipt binds exact release-package digest;
- production adapter remains fail closed unless an approved zero-incremental-cost production path is separately authorized.

## C. Offline/shadow live verification

After shadow deployment, verify the materialized shadow outputs against the locked route manifest without using or changing a public/live route.

At minimum verify:

- exactly 11 required outputs exist;
- each deployed output digest matches its manifest digest;
- current/latest/dated story order parity remains exact;
- six story routes remain permanent and complete;
- media, Watchlist, Professional Series bridge, image, and rating-contract semantics remain unchanged;
- archive/feed membership remains consistent;
- structural/accessibility checks remain passing;
- no extra route is silently introduced;
- deployment identity and verification receipt bind the same release package.

Produce one durable live-verification receipt with `verification_scope=shadow_offline`.

## D. Bounded lifecycle execution

Add a bounded Iteration 6 execution path through the canonical entry point that:

1. requires the locked Iteration 5 route manifest;
2. reuses all locked Iteration 1–5 artifacts;
3. transitions through the existing `Releasing` state;
4. creates/reuses only the release package and shadow deployment materialization;
5. transitions to `Deployed`;
6. performs offline/shadow verification;
7. transitions to `LiveVerified`;
8. stops there with a bounded Iteration 6 completion status.

Do not execute post-publication book evaluation, Command Center projection, final completion, production publishing, or cutover in Iteration 6.

## E. Recovery requirements

Inject failures proving targeted recovery for at least:

- release-package assembly after earlier locked artifacts are already reusable;
- one shadow deployment output after other outputs are materialized;
- final offline/shadow verification after deployment is complete.

A fresh engine instance must resume without chat/session context.

Required anti-rework result:

- zero discovery reexecution;
- zero editorial reexecution;
- zero media reexecution;
- zero Watchlist reexecution;
- zero bridge reexecution;
- zero accepted-image rework;
- zero publication-bundle rebuild;
- zero reader-render rebuild;
- zero route-manifest rebuild;
- zero already materialized unrelated deployment-output rewrite during targeted recovery;
- zero full-pipeline restart.

## F. Fail-closed requirements

Fail closed if:

- the route manifest is missing, invalidated, stale, schema-incompatible, corrupted, or not passing;
- the reader-render digest no longer matches the route manifest;
- a route/output digest differs;
- the release package is incomplete or corrupted;
- a shadow deployment receipt does not bind the release package;
- offline verification detects missing, extra, reordered, or corrupted output;
- any attempt is made to use a production deployment adapter without explicit approved zero-incremental-cost authorization.

## G. Telemetry

Persist bounded Iteration 6 telemetry for:

- release-package attempts/reuse;
- shadow deployment output attempts/retries/cache reuse;
- verification checks/failures by invariant;
- deployment receipt reuse;
- elapsed time;
- anti-rework counters.

Volatile telemetry must remain outside semantic artifact identity.

## Explicit non-scope

Iteration 6 must **not**:

- deploy to GitHub Pages;
- deploy to or mutate a public ChatGPT Site;
- change any live/public URL;
- perform real public-route verification;
- project to the private Command Center;
- implement Command Center UI;
- create or modify production schedules;
- change subscriber delivery;
- migrate legacy historical content;
- cut over production;
- decommission the legacy system;
- modify or interrupt `gttome/Daily-AI-Brief`;
- add a separately billed OpenAI API, paid deployment/hosting API, or other incremental paid production dependency.

## Required proof

At minimum prove:

1. deterministic release-package replay;
2. exact 11-route package parity;
3. deterministic shadow deployment identity;
4. exact output-digest verification after materialization;
5. story/media/Watchlist/bridge/image/rating parity retained;
6. archive/feed parity retained;
7. structural/accessibility parity retained;
8. fail-closed corrupted/stale route manifest;
9. fail-closed corrupted shadow output;
10. targeted release-package recovery;
11. targeted one-output deployment recovery;
12. targeted verification recovery;
13. fresh-engine/no-chat resume;
14. zero reexecution of locked Iteration 1–5 work;
15. no public deployment, live URL mutation, schedules, migration, cutover, or production publication.

## Exit gate

Iteration 6 is complete only after **three consecutive synthetic/shadow release-only runs**, each beginning from a valid locked Iteration 5 route manifest, independently produce without manual intervention:

- one deterministic locked release package;
- one deterministic shadow deployment receipt;
- one passing offline/shadow verification receipt;
- exact route/output parity;
- identical semantic package/deployment identities for identical locked inputs;
- zero unrelated locked-stage reexecution;
- final lifecycle state `LiveVerified`;
- no post-publication evaluation;
- no Command Center projection;
- no public deployment or live-route mutation;
- no production publication.

Merge only the exact candidate that passes the complete regression + Iteration 6 suite. After merge, verify `main` CI again.

## Required closure records

Iteration 6 must follow `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Finish by creating and merging all four required closure artifacts:

- `docs/ITERATION6_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 6 evidence under `evidence/iteration6/`;
- authoritative `docs/ITERATION7_HANDOFF_2026-09-21.md`;
- standalone ready-to-paste `docs/ITERATION7_START_PROMPT_2026-09-21.md`.

Do not report Iteration 7 as ready until all four artifacts are present on verified `main`.
