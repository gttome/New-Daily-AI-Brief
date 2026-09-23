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

## Non-negotiable Iteration 32 mission — testing access only

Iteration 32 has one purpose: **make the greenfield system available for the owner's hands-on testing**.

Implement only the minimum needed to provide:
1. a functioning greenfield Daily Generative AI Brief reader site;
2. a functioning private greenfield Command Center;
3. real owner-accessible URLs for both;
4. basic desktop and phone/small-screen access verification;
5. representative end-to-end data sufficient to exercise the deployed system;
6. the minimum reader surfaces needed for meaningful testing: current edition/home, navigation, archive/history, Watchlist, article/media, ratings, and sharing;
7. the minimum Command Center surfaces needed for meaningful testing: run identity/status, QA/readiness, freshness/currentness, and recovery/resume state;
8. coexistence with the current production Daily AI Brief, with no cutover or production reader routing.

As soon as those URLs and minimum test surfaces are available and verified, **stop and hand control to me for testing**. Do not continue with unrelated features, broader hardening, production cutover, Iteration 32 closure, or Iteration 33 preparation until I provide my testing results and explicitly tell you to continue.

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

## CI runtime constraint before owner testing

Do not make the broader CI-performance optimization a prerequisite to first owner access unless a specific CI defect prevents the test deployment. Preserve safety checks, avoid duplicate exact-head CI, and use the bounded metadata path where applicable. The broader 53–81 minute CI optimization is deferred until after my hands-on testing so Iteration 32 remains focused only on enabling testing.

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

Proceed autonomously only through:
1. verified baseline;
2. the minimum reader and private Command Center implementation needed for hands-on testing;
3. representative data integration;
4. deployment to real owner-accessible URLs;
5. basic desktop and phone/small-screen access checks;
6. the minimum verification needed to ensure the test environment is safe and does not affect production;
7. delivery of both URLs and a concise owner test checklist.

Then **STOP**. Do not close Iteration 32 and do not begin Iteration 33. Wait for my testing results and explicit instruction to continue.

Do not ask me to approve intermediate technical choices when repository contracts already determine a safe option. Make the lowest-complexity, zero-incremental-cost choice that gets the system into a testable state while preserving the existing production system.
