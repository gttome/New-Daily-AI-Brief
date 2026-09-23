@GitHub Proceed with Iteration 32 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use current `main` as the sole source of truth. Before changing anything, independently verify the current main SHA and Greenfield Contracts state, verify Iteration 31 is completely closed and passing, and read:

- `docs/ITERATION32_HANDOFF_2026-09-21.md`
- `docs/ITERATION31_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration31/synthetic-shadow-production-integration-execution-executor-binding-authorization-package-readiness-authorization-package-evidence.json`
- `docs/ITERATION31_PROCESS_HARDENING_AND_ACCESS_AMENDMENT_2026-09-23.md`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`
- `evidence/iteration31/progress.json`

The Iteration 32 handoff is controlling. Do not begin if Iteration 31 evidence reports `repository_closure_status=pending`, `iteration32_ready=false`, any mandatory closure artifact is missing, or current main Greenfield Contracts is not passing. Establish the baseline solely from reconciled repository records, never chat history or a remembered SHA.

Preserve all locked Iterations 1–31 architecture, contracts, identities, lifecycle/state-machine behavior, the canonical `start_daily_brief(date, mode)`, the single `RunEngine`, lease/idempotency, content-addressed records, dependency invalidation, recovery evidence, and exact Iteration 31 authorization-package artifact. Do not rebuild or reexecute completed Iterations 1–31 merely because this is a new chat or because a retry occurs.

## Non-negotiable Iteration 32 mission

Iteration 32 is the fixed first owner-access and acceptance-testing milestone. It may not be replaced by another synthetic-only authorization/readiness gate and may not be deferred to Iteration 33 or later.

By the end of Iteration 32, provide:

1. a functioning greenfield Daily Generative AI Brief reader site;
2. a functioning private greenfield Command Center;
3. real owner-accessible URLs for both surfaces;
4. desktop and phone/small-screen access verification for both URLs;
5. representative end-to-end brief data flowing through the greenfield architecture;
6. usable reader home/current-edition, archive/history, Watchlist, article, media, ratings, sharing, and navigation surfaces required for acceptance testing;
7. observable representative run/QA/readiness/freshness/recovery state in the private Command Center;
8. clear coexistence with the current production Daily AI Brief, with no production cutover or reader routing;
9. an owner-facing acceptance checklist with explicit pass/fail results.

A local-only build, fixture-only artifact, screenshot-only proof, or another synthetic authorization/readiness record is not sufficient to close Iteration 32. Actual deployed URLs must be tested.

## Process-hardening requirements

Retain the Iteration 31 hardening:
- preserve the required **Greenfield Contracts** check name and contract;
- executable/runtime/schema/fixture/test/workflow changes receive the full regression/recovery suite;
- documentation/evidence-only closure and reconciliation use the bounded metadata validator;
- maintain a durable machine-readable iteration checkpoint;
- retries must inspect and reuse existing main/branch/PR/exact-head CI/merge/closure work;
- never create duplicate PRs or duplicate exact-head CI solely because a chat restarted;
- persist closure transitions;
- record elapsed CI times and anti-rework evidence.

If an Actions query helper does not expose push-triggered runs, inspect the GitHub Actions runs API directly rather than assuming no post-merge run exists.

## Safety and cost constraints

Do not:
- cut over production traffic;
- route current readers to greenfield;
- decommission the current production system;
- modify `gttome/Daily-AI-Brief`;
- alter production schedules or subscriber delivery;
- expose private Command Center data, credentials, secrets, private IDs, or prompts;
- add incremental paid services or separately billed dependencies;
- use a real production executor/target merely to satisfy the access milestone;
- weaken CI, recovery, privacy, or fail-closed contracts.

Use existing/no-incremental-cost deployment mechanisms. Representative test data may remain shadow/pre-cutover, but it must exercise the actual deployed greenfield surfaces.

## Required execution

Proceed autonomously through:
1. verified baseline;
2. implementation of the owner-access reader and private Command Center surfaces;
3. representative data integration;
4. desktop and phone acceptance checks against actual URLs;
5. exact-candidate PR and Greenfield Contracts verification;
6. guarded exact-head merge;
7. independent post-merge `main` verification;
8. all four mandatory Iteration 32 closure artifacts;
9. closure CI/merge/reconciliation.

Do not ask me to approve intermediate technical choices when the repository contracts already determine a safe option. Make the lowest-complexity, zero-incremental-cost choice consistent with the handoff and preserve the existing production system.

Iteration 32 must not be declared complete until the working reader URL and private Command Center URL are both provided to me and the documented access/acceptance checks pass. No Iteration 33 prerequisite may be inserted before that first owner access.
