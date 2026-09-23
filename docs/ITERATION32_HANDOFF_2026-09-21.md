# New Daily AI Brief — Iteration 32 Handoff
## Fixed Owner-Access and Acceptance-Testing Milestone

Prepared September 23, 2026. Repository: `gttome/New-Daily-AI-Brief`.

> **ACTIVATION STATUS: PENDING ITERATION 31 REPOSITORY CLOSURE.** Do not begin Iteration 32 until the Iteration 31 evidence reports `repository_closure_status=complete`, `iteration32_ready=true`, all four Iteration 31 closure artifacts exist on verified `main`, and the current Greenfield Contracts check is passing.

## Required startup reads
Use current `main` as the sole source of truth. Independently verify the current main SHA and Greenfield Contracts state, then read:
- `docs/ITERATION32_HANDOFF_2026-09-21.md`
- `docs/ITERATION31_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration31/synthetic-shadow-production-integration-execution-executor-binding-authorization-package-readiness-authorization-package-evidence.json`
- `docs/ITERATION31_PROCESS_HARDENING_AND_ACCESS_AMENDMENT_2026-09-23.md`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`
- `evidence/iteration31/progress.json`

Do not reconstruct the baseline from chat history or a remembered SHA. Resume only from repository records.

## Fixed Iteration 32 mission — testing access only
Iteration 32 has exactly one mission: **make the greenfield system available to the owner for hands-on testing**. It may not be expanded into a general hardening, optimization, feature-completion, cutover, or closure iteration before the owner tests it.

Implement only the minimum work required to provide:
1. a functioning greenfield Daily Generative AI Brief reader site;
2. a functioning private greenfield Command Center;
3. real URLs the owner can open on desktop and phone;
4. representative end-to-end brief data sufficient to exercise the deployed greenfield architecture;
5. the reader surfaces necessary for meaningful testing: current edition/home, navigation, archive/history, Watchlist, article/media, ratings, and sharing;
6. the Command Center surfaces necessary for meaningful testing: run identity/status, QA/readiness, freshness/currentness, and recovery/resume visibility;
7. safe coexistence with the current production Daily AI Brief, with no production cutover or reader routing.

Once these testable URLs and minimum acceptance surfaces are available and verified, **stop and hand control to the owner for testing**. Do not continue with unrelated improvements, broader hardening, additional feature work, production cutover, Iteration 32 closure, or Iteration 33 preparation until the owner reports testing results and explicitly tells the implementation to continue.

## Non-negotiable exit gate
Iteration 32 is not complete until all of the following are true:
- the reader URL exists, resolves, and is owner-accessible on desktop and phone;
- the private Command Center URL exists, resolves, and is owner-accessible on desktop and phone;
- the reader contains representative greenfield data and required navigation/archive/Watchlist/article/media/ratings/share surfaces;
- the Command Center shows representative greenfield run/QA/readiness state and does not expose credentials, secrets, private IDs, prompts, or prohibited private information;
- access tests are performed against the actual URLs, not only local fixtures or static mocks;
- the current production Daily AI Brief remains intact and separately accessible;
- no production cutover, reader routing, legacy decommission, or production publication occurs;
- no incremental paid dependency is introduced;
- the owner-facing acceptance checklist exists and all mandatory technical access checks pass.

A local-only build, synthetic artifact, fixture-only demonstration, screenshot-only proof, or another authorization/readiness record is insufficient.

## Architecture to preserve
Preserve all locked Iterations 1–31 contracts, identities, lifecycle/state-machine semantics, canonical `start_daily_brief(date, mode)`, single `RunEngine`, lease/idempotency behavior, content-addressed records, dependency invalidation, recovery receipts, and the exact Iteration 31 authorization-package artifact.

Do not rebuild or reexecute completed Iterations 1–31 merely to create UI/access surfaces. Reuse durable records and representative fixtures/data where appropriate.

## Process-hardening requirements
The Iteration 31 hardening rules remain active:
- use the existing required **Greenfield Contracts** check;
- full regression for executable/contract changes;
- bounded closure validation for documentation/evidence-only closure/reconciliation changes;
- maintain an authoritative progress checkpoint;
- on retry, inspect and reuse existing branch/PR/exact-head CI/merged work/closure artifacts;
- do not create duplicate PRs or duplicate exact-head CI runs;
- preserve explicit resumable transitions;
- record elapsed CI time and anti-rework evidence.

## CI runtime constraint during Iteration 32
Do not undertake the broader CI-optimization program before owner testing unless it is strictly necessary to reach the testable deployment. Preserve the existing safety checks, avoid duplicate CI runs, and use the existing bounded docs/evidence path. The broader 53–81 minute CI optimization remains required work after owner testing, informed by the owner's findings, rather than a prerequisite to first access.

## Implementation approach
Implement only what is necessary to make the owner-accessible greenfield reader and private Command Center usable for acceptance testing.

Prefer the repository's existing no-incremental-cost deployment mechanisms and existing architecture. If multiple zero-cost deployment approaches are possible, choose the one that:
- produces stable owner-accessible URLs;
- preserves privacy for the Command Center;
- does not alter the current production Daily AI Brief;
- requires the fewest new moving parts;
- can be verified deterministically.

Representative data may be synthetic/shadow/pre-cutover data, but it must exercise the actual greenfield reader and Command Center surfaces end-to-end.

## Required reader acceptance surface
At minimum verify:
- home/current edition;
- archive/history access;
- Watchlist;
- article detail;
- video/media and podcast surfaces where represented by the greenfield model;
- ratings interaction;
- sharing interaction;
- navigation between these surfaces;
- responsive usability on desktop and phone;
- clear pre-cutover/shadow labeling where needed so the owner cannot mistake greenfield test content for production publication.

## Required private Command Center acceptance surface
At minimum verify:
- current representative run/edition identity;
- lifecycle/phase status;
- QA/readiness state;
- freshness/currentness;
- recovery/resume state;
- clear production-vs-greenfield separation;
- no credential/secret/private-ID/prompt exposure;
- responsive owner usability on desktop and phone.

## Required verification
Use actual deployed URLs for final access proof. Record:
- deployment identities and URLs;
- exact source commit SHA;
- Greenfield Contracts results;
- desktop access checks;
- phone/small-screen access checks;
- representative data verification;
- reader surface checks;
- Command Center surface checks;
- coexistence check against current production;
- privacy/safety checks;
- recovery/resume proof where deployment work can fail;
- zero prior-iteration rebuild/reexecution;
- zero incremental paid dependency.

## Explicit non-scope
Do not:
- cut over production traffic;
- route current readers to greenfield;
- decommission or modify the legacy production system unless explicitly required by a later approved cutover iteration;
- change `gttome/Daily-AI-Brief`;
- change production schedules or subscriber delivery;
- use production credentials in repository fixtures or logs;
- expose private Command Center data publicly;
- add incremental paid services;
- weaken CI or safety contracts.

## Owner-testing stop gate
Iteration 32 reaches its required interim stop point when:
1. the minimum testable reader and private Command Center are deployed;
2. both actual URLs are provided to the owner;
3. basic desktop and phone/small-screen access checks pass;
4. representative data is visible;
5. the required minimum reader and Command Center test surfaces are usable;
6. the current production system remains unaffected.

At that point, **stop work and wait for the owner's testing results**. Do not close Iteration 32, do not create Iteration 33, and do not add work beyond what is required to enable testing. Post-testing fixes, broader CI optimization, remaining hardening, and final Iteration 32 closure may proceed only after the owner explicitly resumes the iteration.
