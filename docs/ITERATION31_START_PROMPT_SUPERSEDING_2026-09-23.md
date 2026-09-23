@GitHub Proceed with Iteration 31 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

This prompt **supersedes** `docs/ITERATION31_START_PROMPT_2026-09-21.md` for startup/process requirements. The technical Iteration 31 gate remains defined by the authoritative handoff, supplemented by the process-hardening and user-access amendment.

Use current `main` as the sole source of truth. Before changing anything, independently verify current main SHA and Greenfield Contracts CI, verify Iteration 30 is completely closed and passing, and read:

- `docs/ITERATION31_HANDOFF_2026-09-21.md`
- `docs/ITERATION31_PROCESS_HARDENING_AND_ACCESS_AMENDMENT_2026-09-23.md`
- `docs/ITERATION30_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration30/synthetic-shadow-production-integration-execution-executor-binding-authorization-package-readiness-authorization-decision-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

Do not begin if Iteration 30 reports `repository_closure_status=pending`, `iteration31_ready=false`, required closure records are missing, or current main CI is not passing. Establish the baseline only from reconciled repository records, never chat history or a remembered SHA.

## First: unnumbered process-hardening prelude

Before implementing the Iteration 31 gate, implement the process-hardening requirements in `docs/ITERATION31_PROCESS_HARDENING_AND_ACCESS_AMENDMENT_2026-09-23.md` on the same Iteration 31 branch/PR sequence. This is **not Iteration 32** and must not create another numbered iteration.

The prelude must:
- add path-aware CI while preserving the repository's required CI check contract;
- keep the full Greenfield Contracts runtime/recovery suite for executable/contract-bearing changes;
- use a bounded closure-metadata validation path for docs/evidence-only closure/reconciliation changes when runtime code, schemas, fixtures, tests, and workflow logic are unchanged;
- add an authoritative durable machine-readable iteration progress/checkpoint record;
- make retry/resume idempotent so completed work, existing PRs, exact-head CI runs, merged commits, and closure artifacts are reused rather than recreated;
- make closure state transitions explicit and resumable;
- record CI elapsed-time evidence demonstrating the improvement;
- preserve runtime safety coverage.

Do not redo or rebuild any completed Iterations 1–30 work. A user message such as “retry”, “continue”, or “status” must resume from the last authoritative repository checkpoint.

## Then: Iteration 31 bounded implementation

Preserve the Iterations 1–30 lifecycle, state machine, canonical `start_daily_brief(date, mode)`, single `RunEngine` owner, lease/idempotency, content-addressed locks/digests, dependency invalidation, incident/recovery receipts, completion primitives, exact locked Iteration 30 authorization-decision artifact/policy/manifest/separate-decision/ordered decision-evidence identities, exact locked Iteration 29 authorization-review identities/evidence, exact locked Iteration 28 rehearsal identities/receipts, exact locked Iteration 27 preflight identities/evidence, exact Iteration 26 readiness identity/evidence inventory, exact Iteration 25 authorization-package identity/evidence inventory, exact Iteration 24 authorization-decision identity/evidence inventory, and every required transitive identity.

Implement Iteration 31 only: the deterministic synthetic-only executor-binding authorization-package-readiness authorization-package gate defined in `docs/ITERATION31_HANDOFF_2026-09-21.md`.

Keep the current repository blocked. Require a separate independently digestible synthetic authorization-package record and bounded ordered synthetic package-evidence inventory for any package-complete proof. Add one mutually exclusive bounded authorization-package-only path through the canonical owner; do not introduce a second orchestrator.

Prove deterministic replay, exact source/transitive binding, all required fail-closed cases, three independent shadow exit runs, and fresh-engine recovery from authorization-package evaluation, targeted package-evidence validation, and final artifact assembly with zero Iterations 1–30 reexecution, zero Iteration 30 rebuild, durable evidence reuse, zero unrelated rewrites, and zero full-pipeline restart.

Do not implement/bind/invoke a real executor, use/store production credentials, contact a real target, grant/execute production or rollback/cutover/decommission/publication authority, mutate the production/private Command Center, deploy the production reader, change live public URLs, run production schedules, change subscriber delivery, migrate/cut over/decommission legacy, route production readers to greenfield, publish to production, modify `gttome/Daily-AI-Brief`, or add separately billed/incremental paid dependencies. Missing repository-authoritative zero-cost approval must fail closed.

Continue through implementation, deterministic/recovery tests, exact-candidate PR/CI, guarded exact-head merge, and independent post-merge verification. Then create and merge all four mandatory Iteration 31 closure artifacts required by `docs/ITERATION_START_PACKAGE_STANDARD.md`.

## Non-negotiable Iteration 32 handoff requirement

The Iteration 31 closure package must define **Iteration 32 as the fixed user-access milestone**. Do not create another synthetic-only gate as the sole Iteration 32 mission and do not defer first user access to Iteration 33 or later.

The Iteration 32 handoff/start prompt must require, as its exit gate:
- an accessible working greenfield Daily Generative AI Brief reader site;
- an accessible private greenfield Command Center;
- real owner-testable desktop and phone URLs;
- representative end-to-end greenfield brief data;
- reader navigation/archive/Watchlist/article/media and required ratings/sharing surfaces sufficient for meaningful acceptance testing;
- Command Center run/QA/readiness visibility;
- coexistence with the current production system;
- an owner acceptance checklist.

Iteration 32 may be shadow/pre-cutover and must not endanger the existing production system, but **Iteration 32 may not be reported complete until those working URLs exist and the documented access checks pass.**

No later iteration may be inserted as a prerequisite for first owner access to the working greenfield system.

Report:
- exact starting main SHA and CI;
- process-hardening changes and proof that retries resume without duplicate work;
- path-aware CI behavior and measured runtime improvement;
- Iteration 31 implementation PR/candidate/tree/CI/merge/post-merge identities;
- three-run exit results and recovery/anti-rework proof;
- all four Iteration 31 closure paths;
- reconciled `iteration32_ready` state;
- explicit confirmation that the Iteration 32 handoff contains the fixed user-access exit gate above.
