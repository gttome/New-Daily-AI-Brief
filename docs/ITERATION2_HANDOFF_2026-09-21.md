# New Daily AI Brief — Iteration 2 Handoff
## Discovery & Editorial Module
### Prepared September 21, 2026

## Starting point

Iteration 1 established and merged the canonical greenfield control plane in `gttome/New-Daily-AI-Brief`. The Iteration 1 implementation baseline is commit `cf276759cb49a46baf1ea491ca8f956bd957c075`; GitHub Actions run `35667285745` passed all 15 contract/recovery tests.

The control plane includes:

- durable run state and legal transitions;
- lease/idempotent entry;
- immutable content-addressed locks;
- descendant-only invalidation;
- incident/recovery receipts;
- completion/book-evaluation/rating/watermark primitives;
- manual and future-scheduled starts through the same `start_daily_brief(date, mode)` entry point;
- deterministic restart/replay tests.

Read before changes:

1. `docs/ITERATION1_AFTER_ACTION_2026-09-21.md`;
2. `docs/ITERATION1_SIMPLIFICATION_REVIEW.md`;
3. `docs/SCHEMA_VERSION_POLICY.md`;
4. `evidence/iteration1/synthetic-recovery-evidence.json`;
5. the approved September 21 pre-implementation decision record and original greenfield design package.

## Iteration 2 mission

Produce a high-quality **six-story canonical edition without publication** using the Iteration 1 engine rather than adding a second orchestrator.

## Build only

- versioned source registry needed for editorial discovery;
- due-source / metadata-first discovery primitives;
- freshness checks;
- compact novelty index;
- bounded fallback tiers;
- evidence packets with provenance;
- deterministic exact 2/2/2 allocation;
- exactly one reusable Agent Skills story;
- editorial lock as a canonical `edition` artifact;
- discovery/editorial metrics: scans, deep retrieval count, elapsed time, candidate count, cache behavior, fallback use.

## Architecture rules

- Do not create a second state machine or schedule.
- Discovery and editorial selection run inside the existing `Acquiring`/`Deciding` stages.
- Locked Iteration 1 artifacts and dependency rules remain authoritative.
- One bad candidate/source may invalidate only its affected editorial descendants.
- Chat is not state.
- No separately billed API or new metered service.
- Do not implement images, media research, Watchlist source traversal, public rendering, Command Center UI, deployment, or cutover in Iteration 2.
- The legacy system is evidence and product requirements only; do not port its workflow topology.

## Reliability tests required

At minimum prove:

- metadata fetch failure retries/falls back within bounded policy;
- candidate shortage expands only the affected tier/category;
- freshness failure rejects only the affected candidate;
- exact/normalized prior-URL novelty collision is rejected;
- related-but-distinct development remains eligible;
- semantic agent classification recognizes reusable Agent Skills;
- exact 2/2/2 allocation and one Agent Skills story;
- a failed editorial candidate does not re-run unrelated locked work;
- process restart resumes discovery/editorial state from durable records;
- same locked evidence/configuration reproduces the same edition digest.

## Exit gate

Iteration 2 is complete only when **three consecutive synthetic or shadow discovery/editorial runs** produce six valid stories with the exact 2/2/2 allocation and one reusable Agent Skills story, without manual intervention and without publishing anything.

## Launch prompt

```text
@GitHub Proceed with Iteration 2 of the New Daily AI Brief greenfield implementation using `docs/ITERATION2_HANDOFF_2026-09-21.md` in `gttome/New-Daily-AI-Brief`.

Start from the merged Iteration 1 control plane. Do not redesign or bypass its state machine, lock/digest mechanism, dependency invalidation, recovery receipts, completion primitives, or canonical `start_daily_brief(date, mode)` entry point.

Implement Iteration 2 only: the source registry needed for editorial discovery, metadata-first/due-source discovery, freshness, novelty, bounded fallbacks, evidence packets, deterministic exact 2/2/2 story allocation, exactly one reusable Agent Skills story, editorial locking, and the required discovery/editorial telemetry and recovery tests.

Do not implement images, media research, Watchlist source traversal, public Site rendering, Command Center UI, deployment, production schedules, or cutover. Do not introduce a paid API or other incremental paid production dependency. Do not clone or port the legacy backend workflow topology.

Use synthetic fixtures first. Prove targeted failure recovery, no-chat resume, no unrelated locked-stage reexecution, and deterministic edition replay. Iteration 2 is complete only after three consecutive synthetic/shadow discovery runs produce six valid stories in the approved allocation without manual intervention. Finish with an Iteration 2 after-action report and Iteration 3 handoff.
```
