# New Daily AI Brief — Greenfield Implementation

This repository is the clean-room replacement for the Daily AI Brief backend. It is **not** a clone or refactor of `gttome/Daily-AI-Brief`.

## Iteration 1

Iteration 1 implements only the canonical control plane:

- versioned JSON contracts;
- one durable run record;
- edition/mode lease and idempotent start;
- legal state transitions;
- content-addressed locked artifacts;
- dependency-driven descendant invalidation;
- incident and recovery receipts;
- completion receipts;
- mandatory private book-change evaluation contract;
- five-star rating contract/version primitive;
- Command Center projection freshness watermark;
- a single `start_daily_brief(date, mode)` entry point for manual and future scheduled starts;
- deterministic synthetic failure, restart, recovery, and replay tests.

No live discovery, real editorial selection, image generation, media research, public rendering, schedule changes, paid API dependency, or production cutover is included.

## Run locally

```bash
PYTHONPATH=src python -m new_daily_ai_brief run-now \
  --date 2026-09-22 \
  --mode synthetic \
  --state-dir .state
```

Inject a validation failure:

```bash
PYTHONPATH=src python -m new_daily_ai_brief run-now \
  --date 2026-09-22 \
  --mode synthetic \
  --state-dir .state \
  --inject-failure Validating
```

Then invoke the same command again without `--inject-failure`; the engine resumes from durable `Recovering` state and preserves unaffected locks.

## Test

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

## State model

`Ready → Acquiring → Deciding → Building → Validating → Releasing → Deployed → LiveVerified → PostPublicationEvaluation → OperationsReconciled → Complete`

Recoverable failures enter `Recovering` and may return only to the failed state family. Chat is never operational state.
