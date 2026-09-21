# New Daily AI Brief — Iteration 3 Handoff
## Build-Stage Enrichment: Media, Watchlist & Book Bridges
### Prepared September 21, 2026

## Starting point

Iteration 2 implementation is merged on `main` at `5af854521898c3aa0971149b16c56f798a7c1e66`. PR #3 and post-merge main CI both passed the 24-test Python 3.11 suite.

Iterations 1 and 2 provide one control plane plus a deterministic locked six-story edition:

- canonical `start_daily_brief(date, mode)`;
- durable lifecycle, lease/idempotency, artifact locking, dependency invalidation, incidents/recovery receipts;
- metadata-first discovery, freshness, novelty, bounded fallback, evidence packets;
- exact 2/2/2 allocation and exactly one reusable Agent Skills story;
- deterministic `discovery` and `edition` locks;
- no-chat targeted recovery.

Read the Iteration 1 and 2 after-action reports, schema policy, and synthetic evidence before changes.

## Mission

Implement the next bounded work inside the existing `Building` state **without publication**:

1. verified media selection producing exactly **2 videos and 2 podcasts**;
2. canonical Watchlist daily delta;
3. centralized, relevant Generative AI Professional Series book-bridge decisions.

Do not create another orchestrator or lifecycle.

## Build only

### Media
- versioned source/config registry;
- metadata-first discovery and availability verification;
- exactly 2 verified videos and 2 verified podcasts;
- evidence/provenance for each item;
- deterministic media lock tied to the edition digest;
- bounded item/source fallback.

### Watchlist
- source traversal needed for the canonical daily delta;
- explicit `new_today`, `updated_today`, and `carried_forward` semantics;
- provenance for changed topics;
- date-current output; no stale edition reuse;
- deterministic Watchlist lock.

### Professional Series bridges
- one centralized, versioned mapping representation;
- reader-facing bridge only when materially relevant;
- explicit no-bridge result when no mapping is warranted;
- do not fabricate or force links;
- keep this distinct from the mandatory post-publication private book-change evaluation.

### Telemetry/recovery
Persist bounded metrics for scans/retrievals, availability failures, Watchlist checks/changes, bridge decisions, fallback use, cache reuse, and elapsed time. Resume from durable records without chat and repair only the failed item/boundary.

## Architecture rules

- Continue using the existing `Building` state.
- The locked `edition` remains immutable upstream input.
- Existing dependency/invalidation rules remain authoritative.
- A failed media item, Watchlist source, or bridge decision may not rerun discovery/editorial work or unrelated locked build work.
- No paid API or new metered production dependency.
- Do not port legacy workflow topology.

## Explicit non-scope

Do **not** implement images, public Site rendering, archive/feed output, Command Center UI, deployment/live verification, production schedules, cutover, or legacy decommissioning.

## Required proof

At minimum test:

- bounded fallback for unavailable video and podcast candidates;
- deterministic exact 2-video/2-podcast media replay;
- deterministic date-correct Watchlist `new/updated/carried` classification;
- targeted Watchlist-source recovery;
- explicit no-bridge behavior;
- deterministic centralized bridge mapping;
- process restart/no-chat resume in Building;
- zero reexecution of locked discovery/editorial work;
- same locked inputs reproduce the same Build-stage artifact digests.

## Exit gate

Iteration 3 is complete only after three consecutive synthetic/shadow Build-stage runs, starting from valid locked Iteration 2 editions, produce without manual intervention:

- exactly 2 verified videos;
- exactly 2 verified podcasts;
- a date-current canonical Watchlist delta;
- complete bridge decisions for all six stories;
- zero discovery/editorial reexecution;
- deterministic replay;
- no images, public rendering, deployment, or publication.

## Launch prompt

```text
@GitHub Proceed with Iteration 3 of the New Daily AI Brief greenfield implementation using docs/ITERATION3_HANDOFF_2026-09-21.md in gttome/New-Daily-AI-Brief.

Start from the merged Iteration 1 control plane and merged Iteration 2 discovery/editorial module. Preserve the existing lifecycle, locks/digests, dependency invalidation, recovery receipts, completion primitives, locked edition, and canonical start_daily_brief(date, mode) entry point.

Implement Iteration 3 only inside Building: bounded verified media selection with exactly 2 videos and 2 podcasts, canonical Watchlist daily delta generation, and centralized relevant Generative AI Professional Series book-bridge decisions. Add provenance, telemetry, targeted recovery, no-chat resume, and deterministic replay tests.

Do not implement images, public rendering, archive/feed output, Command Center UI, deployment, production schedules, cutover, or legacy decommissioning. Do not add a paid API or other incremental paid production dependency. Use synthetic fixtures first.

Finish only after three consecutive synthetic/shadow Build-stage runs meet the Iteration 3 exit gate, then create the Iteration 3 after-action report and next handoff.
```
