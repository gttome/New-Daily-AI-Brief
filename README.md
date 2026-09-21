# New Daily AI Brief — Greenfield Implementation

This repository is the clean-room replacement for the Daily AI Brief backend. It is **not** a clone of `gttome/Daily-AI-Brief`.

## Iteration 1 — canonical control plane

Iteration 1 established the durable lifecycle owner: versioned contracts, one run identity, lease/idempotency, legal state transitions, content-addressed locks, descendant-only invalidation, incident/recovery receipts, completion primitives, five-star rating contract, projection watermark, and the single `start_daily_brief(date, mode)` entry point.

## Iteration 2 — discovery & editorial

Iteration 2 extends the same control plane. Synthetic/shadow mode now provides:

- versioned source registry and bounded discovery policy;
- due-source, metadata-first acquisition;
- freshness and compact novelty checks;
- category-local bounded fallback;
- provenance-bearing content-addressed evidence packets;
- deterministic exact 2/2/2 story allocation;
- exactly one reusable Agent Skills story;
- a canonical locked `discovery` artifact in `Acquiring`;
- a canonical locked `edition` artifact in `Deciding`;
- durable telemetry and targeted no-chat candidate recovery.

Production discovery is intentionally **fail closed** during Iteration 2. Editorial-only validation stops at the existing `Building` boundary with `completion_status=editorial_locked`. It does not execute media, images, Watchlist, publication, deployment, rendering, Command Center UI, schedules, or cutover.

## Test

```bash
PYTHONPATH=src python -m compileall -q src tests
PYTHONPATH=src python -m unittest discover -s tests -v
```

Iteration 2 evidence: `evidence/iteration2/synthetic-discovery-editorial-evidence.json`.

## State model

`Ready → Acquiring → Deciding → Building → Validating → Releasing → Deployed → LiveVerified → PostPublicationEvaluation → OperationsReconciled → Complete`

Recoverable pre-live failures use the existing `Recovering` boundary. Chat is not operational state.
