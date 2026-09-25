# Testing and Validation Standard

**Document type:** Living engineering and QA standard  
**Repository:** `gttome/New-Daily-AI-Brief`  
**Status:** Active living document  
**Effective date:** 2026-09-24  
**Owner:** New Daily AI Brief  
**Applies to:** all implementation work, PRs, workflows, integrations, migration work, reader work, Command Center work, and release/cutover validation

---

## 1. Purpose

This document separates **development speed** from **comprehensive system assurance**.

The system must retain complete, rigorous testing. However, comprehensive system testing must not be coupled automatically to every bounded development change or implementation iteration.

The required model is:

1. **Development Validation** — fast, change-specific, mandatory for ordinary development.
2. **Integration Validation** — bounded end-to-end validation of affected interfaces when appropriate.
3. **Full System Validation** — comprehensive repository/system regression, run only as its own explicitly requested activity.

This is a living document and must be updated whenever test scope, test ownership, workflows, change-impact routing, validation gates, failure-injection coverage, or full-system validation behavior changes.

---

## 2. Core policy

### 2.1 An iteration is not a full-system regression

A development iteration means:

`implement bounded capability → run required affected tests → run bounded integration tests when needed → merge`

It does not mean:

`implement one change → replay the entire historical system → run every fixture → rebuild all history → execute full end-to-end regression`

### 2.2 Complete testing remains mandatory

This standard does not remove comprehensive testing.

Instead, it moves comprehensive validation into a dedicated, explicit activity:

**Full System Validation**

That activity is not implicitly attached to any single implementation iteration.

### 2.3 Test scope must follow change impact

Ordinary development testing must be selected from the component(s) actually changed and their immediate dependency cone.

### 2.4 Expensive historical tests are not development smoke tests

Historical parity, broad migration replay, complete archive/feed reconstruction, full failure-injection suites, and all-iteration fixture replay belong in Full System Validation unless the specific development change directly affects those areas.

### 2.5 Required checks may never be bypassed to save time

A test may be excluded from an ordinary development change only because the change-impact model demonstrates that it is outside the affected dependency cone—not merely because it is slow.

---

## 3. Three validation levels

## Level 1 — Development Validation

### Purpose

Provide rapid feedback that the specific code/configuration/data change works and preserves the local contract it modifies.

### Trigger

Runs automatically for every development PR or material change.

### Expected scope

Only:

- changed component;
- changed schemas/contracts;
- immediate upstream/downstream dependencies;
- representative fixtures needed to prove the change;
- privacy/security checks relevant to the changed area.

### Examples

| Change | Required Development Validation |
|---|---|
| Command Center CSS/HTML | syntax, DOM contract, responsive/mobile checks, accessibility checks relevant to changed UI |
| Command Center adapter | adapter unit tests, schema validation, representative data fixtures, privacy/missingness tests |
| Command Center state schema | schema tests, adapter compatibility tests, representative projection fixture |
| Editorial selection | candidate-selection tests, novelty logic, 2/2/2 allocation, exactly-one Agent Skills |
| Discovery | discovery unit tests, evidence packet behavior, bounded retrieval/fallback fixture |
| Media | media source/verification tests |
| Images | image contract, six-image binding, quality-gate fixture |
| Reader rendering | renderer tests, affected routes, one representative edition |
| Watchlist | topic-state, source-state, update/carry-forward tests |
| Workflow YAML | syntax, dispatch inputs, contract/dry fixture |
| RunEngine stage | stage tests, legal transitions, immediate downstream artifact binding |
| Shared schema/contract | contract tests plus direct consumer compatibility |
| Private data | CRUD, dedupe, privacy, persistence, missingness |

### Explicitly excluded by default

Development Validation must not automatically run:

- every historical edition;
- all historical migration replay;
- every Iteration 1–32 fixture;
- all legacy authorization/rehearsal fixtures;
- complete archive/feed history reconstruction;
- full reader-history parity;
- all failure-injection scenarios;
- complete production-like end-to-end replay;
- system-wide mobile/desktop checks on every route;
- all unrelated components.

Any of these may still be required when the change-impact model says the change directly affects them.

---

## Level 2 — Integration Validation

### Purpose

Prove that the changed component still integrates correctly with its adjacent components and contracts.

### Trigger

Runs automatically or explicitly before merge when the change crosses a component boundary or modifies a shared contract.

### Characteristics

- bounded;
- representative;
- deterministic;
- one or a small number of fixtures;
- no broad historical replay unless history itself is being changed.

### Representative integration paths

#### Daily Brief content path

`representative discovery fixture → canonical editorial selection → build → validation → reader candidate`

#### Command Center path

`canonical greenfield artifacts → Command Center projection → public/private filter → Command Center state → UI render`

#### Publication path

`release package → route manifest → reader bundle → live-verification fixture`

#### Private owner-data path

`private record create → dedupe → update → reload/read → UI state`

### Integration evidence

The PR/closure record should identify:

- integration path exercised;
- fixtures used;
- tested SHA;
- result;
- any limitations.

---

## Level 3 — Full System Validation

### Purpose

Provide comprehensive, auditable assurance that the entire system and its historical/protected behavior remain correct.

### Trigger policy

Full System Validation is a **separate manual/requested activity**.

It must be exposed as its own workflow, for example:

**`Full System Validation`**

The workflow should use `workflow_dispatch` and must not be automatically attached to an ordinary implementation iteration or PR.

### Appropriate reasons to run it

- owner explicitly requests Full System Validation;
- before production cutover;
- after completion of Command Center data parity;
- before decommissioning the current Daily AI Brief;
- after a major RunEngine architecture change;
- after a repository-wide schema migration;
- after a publication architecture change;
- before a major production release;
- when a serious regression indicates system-wide verification is warranted.

### Comprehensive scope

Full System Validation may include:

- complete Python/unit test suite;
- complete contract/schema suite;
- all currently required historical fixtures;
- canonical RunEngine lifecycle;
- state-transition validation;
- failure injection;
- recovery/resume;
- anti-rework validation;
- complete reader parity;
- historical migration validation;
- archive/feed parity;
- story/media/image validation;
- Watchlist history;
- accessibility;
- ratings/share/comment contracts;
- analytics/reader-signal contracts;
- Command Center data parity;
- private/public privacy boundary;
- Usage History;
- Book Change Proposals;
- incidents/corrections/governance;
- desktop/mobile rendering;
- complete route generation;
- release/live verification;
- production-readiness gates;
- protected-history integrity.

### Evidence package

Every Full System Validation run must produce a durable evidence package grouped under a dedicated full-system-validation evidence area by validation date and run ID.

Minimum contents:

- tested repository SHA;
- test-plan/version;
- exact test inventory;
- component results;
- integration results;
- historical parity results;
- privacy results;
- failure-injection results;
- timing by major suite;
- failures/defects;
- unresolved risks;
- final validation disposition.

---

## 4. Change-impact routing

A machine-readable change-impact map must control Development and Integration Validation.

A machine-readable impact map should be created during implementation in the repository's configuration area under the filename **test-impact-map.json**.

The map must relate changed paths/components to:

- required Development Validation suites;
- required Integration Validation suites;
- direct dependency cones;
- optional expensive tests;
- whether a change requires Full System Validation to be recommended later.

Example conceptual mapping:

| Component | Development suites | Integration suites |
|---|---|---|
| Command Center UI | CC UI, accessibility, responsive | CC state → render |
| Command Center adapter | adapter, schemas, privacy | canonical artifacts → projection → state |
| Editorial | editorial, novelty, allocation | discovery → edition |
| Media | media verification | edition → media/build |
| Images | image contract/QA | locked stories → images → reader |
| Reader | renderer/routes | release → reader candidate |
| RunEngine | stage/state-machine tests | affected stage chain |
| Shared schemas | schema/consumer tests | affected producer-consumer pairs |

### Change-classifier rules

The classifier must:

1. inspect changed paths;
2. resolve affected components;
3. resolve direct consumers/producers;
4. select only required suites;
5. output its test decision in CI logs/evidence;
6. fail closed if a changed path has no known classification.

A developer must not be able to make a material change in an unmapped area and silently receive no tests.

---

## 5. PR and iteration closure semantics

Every implementation closure must distinguish the three test levels.

Example:

```text
Development Validation: PASS
Integration Validation: PASS
Full System Validation: NOT REQUESTED
```

`Full System Validation: NOT REQUESTED` is a valid state for ordinary development. It is not a failure or incomplete closure.

Closure evidence must include:

- tested SHA;
- Development Validation suites run;
- Integration Validation suites run;
- test results;
- skipped suites and reason where relevant;
- whether Full System Validation was requested.

---

## 6. Performance rules

### 6.1 Development tests should be intentionally bounded

Development Validation should favor:

- unit tests;
- schema/contract validation;
- synthetic/representative fixtures;
- targeted compilation;
- one representative edition;
- direct affected routes;
- deterministic local data.

### 6.2 Historical replay belongs to the historical test activity

Historical replay is required when:

- historical migration changes;
- append-only behavior changes;
- archive/feed history logic changes;
- historical data contracts change;
- Full System Validation is requested.

Otherwise it is excluded from the normal development loop.

### 6.3 No accidental 50-minute test runs

A bounded change should not trigger a long regression merely because its path appears in a broad workflow condition.

If a Development or Integration Validation job unexpectedly expands into a system-wide run, that is a testing-architecture defect and must be corrected.

### 6.4 Testing telemetry

Validation workflows should record at least:

- selected test level;
- selected suites;
- selection rationale;
- start/end time;
- elapsed time;
- result;
- tested SHA.

This makes slow-growth regressions visible.

---

## 7. Full System Validation workflow design

The repository should contain a dedicated manually dispatched workflow named **Full System Validation**; its workflow filename should be established during implementation.

Required characteristics:

- manual `workflow_dispatch`;
- clearly named **Full System Validation**;
- separate from ordinary PR/iteration workflows;
- does not automatically run because a PR is opened;
- can be explicitly requested against a known SHA/branch;
- produces durable evidence artifacts;
- does not mutate production;
- can report failures without rewriting development checkpoints;
- supports safe rerun of failed suites without redoing completed passing suites where practical.

The workflow should support a clear operator input for reason/context, such as:

- pre-cutover;
- post-data-parity;
- architecture change;
- owner-requested audit;
- incident investigation.

---

## 8. Command Center parity testing

Command Center data parity is important enough to have its own dedicated integration activity.

The repository should expose:

**Command Center Data Parity Validation**

This validation compares the current and new Command Centers by data family rather than by visual appearance.

For every row in the machine-readable Command Center data-parity matrix, it should verify:

- presence;
- semantic equivalence/improvement;
- historical depth;
- authoritative provenance;
- freshness/currentness;
- zero/missing semantics;
- privacy;
- traceability.

This validation is required before Command Center cutover.

It is not a replacement for Full System Validation.

---

## 9. Private-data testing

Private owner-data changes require dedicated tests without exposing private values in public fixtures.

Minimum required coverage:

### Usage History

- multiple history dates;
- merge private and repository attempts;
- dedupe by `attempt_id`;
- idempotent refresh;
- measured zero stays zero;
- missing metric stays unavailable;
- one missing metric does not suppress other measurements;
- invalid negative/nonnumeric measurement rejected individually;
- credits remain unavailable without authoritative evidence;
- reload persistence;
- incompatible measurement boundaries not silently merged.

### Book Change Proposals

- create;
- read;
- update;
- Pending/Approved/Rejected transitions;
- reload persistence;
- stable dedupe;
- idempotent historical import;
- idempotent current-edition evaluation;
- prior decisions preserved;
- no false success on failed write;
- no proposal content leaks into public repository/output.

---

## 10. Failure-injection strategy

Failure injection remains part of comprehensive assurance.

Full System Validation should include the complete maintained failure catalog.

Development Validation should run only the failure cases relevant to the changed component.

Examples:

- broken source → discovery/source changes;
- duplicate story → editorial/novelty changes;
- invalid allocation → editorial changes;
- image failure → image pipeline changes;
- malformed feed → feed/render changes;
- stale/missing Command Center projection → CC adapter changes;
- private persistence failure → private-data changes;
- deployment mismatch → release/deployment changes.

---

## 11. Testing changes that require this document to be updated

This living standard must be updated in the same change set whenever:

- a test suite is added/removed;
- a test moves between Development, Integration, and Full System Validation;
- the change-impact routing changes;
- a new component is introduced;
- a new shared schema changes dependency relationships;
- a failure-injection case is added/removed;
- Full System Validation scope changes;
- a new cutover gate is introduced;
- a new privacy/security validation is introduced;
- validation evidence format changes;
- workflow behavior or triggering changes materially;
- an ordinary development workflow begins running an expensive suite previously reserved for Full System Validation.

A PR that materially changes testing architecture without updating this document is incomplete.

---

## 12. Implementation plan

### Phase 1 — Inventory current test/workflow behavior

- classify all current tests/workflows;
- measure their typical duration;
- map suites to components;
- identify historical/comprehensive suites incorrectly coupled to ordinary development.

### Phase 2 — Build change-impact map

- create `config/test-impact-map.json`;
- map repository paths to affected component suites;
- fail closed for unknown paths;
- record selected suites in CI output.

### Phase 3 — Refactor Development Validation

- make ordinary PR validation bounded;
- remove unrelated historical/full regressions from routine changes;
- preserve all tests in their appropriate tier.

### Phase 4 — Add Integration Validation

- define representative bounded integration paths;
- run them only when a change crosses a relevant boundary.

### Phase 5 — Create Full System Validation workflow

- manual/requested only;
- comprehensive;
- durable evidence;
- rerunnable by suite where practical.

### Phase 6 — Create Command Center Data Parity Validation

- drive from the parity matrix;
- compare current and new data families;
- require zero unexplained gaps before cutover.

### Phase 7 — Prove the new testing architecture

Acceptance proof must demonstrate:

1. a documentation-only change runs no unnecessary regression;
2. a Command Center UI-only change runs bounded CC tests;
3. a Command Center adapter change runs projection/integration tests but not historical full-system replay;
4. a RunEngine stage change runs its dependency cone;
5. Full System Validation does not start unless explicitly requested;
6. manual Full System Validation still runs the comprehensive suite.

---

## 13. Acceptance criteria

The revised testing architecture is complete when:

1. ordinary development uses bounded Development Validation;
2. cross-component changes receive bounded Integration Validation;
3. Full System Validation exists as a separate manual/requested workflow;
4. no implementation iteration automatically launches Full System Validation;
5. all current important tests still exist somewhere in the testing model;
6. the change-impact classifier fails closed on unknown material paths;
7. selected test scope and rationale are visible in CI;
8. development/test closure distinguishes all three validation levels;
9. historical/full regressions run only when relevant or explicitly requested;
10. full-system evidence is permanent and auditable;
11. no Critical/High testing-architecture defect remains.

---

## 14. Living-document maintenance policy

This document is the authoritative testing-policy source.

Any change to:

- testing levels;
- workflow triggers;
- test ownership;
- change-impact routing;
- test suite membership;
- full-system scope;
- failure injection;
- validation gates;
- evidence requirements;

must update this file at the same time.

The document must be reviewed before production cutover and after every major testing-architecture change.

---

## 15. Change log

| Date | Change |
|---|---|
| 2026-09-24 | Initial living testing standard created to separate bounded development/integration testing from explicitly requested Full System Validation. |


---

## 16. Implemented validation control plane

The 2026-09-24 testing-architecture revision implements this standard with these authoritative controls:

- `config/test-impact-map.json` — centralized machine-readable path/component/dependency/suite map.
- `scripts/select_validation.py` — fail-closed changed-path classifier and suite selector.
- `scripts/run_validation.py` — bounded Development/Integration suite runner and telemetry/evidence writer.
- `.github/workflows/ci.yml` — ordinary PR/main Development and Integration Validation only.
- `.github/workflows/full-system-validation.yml` — manual-only **Full System Validation** entry point.
- `.github/workflows/command-center-data-parity-validation.yml` — dedicated bounded **Command Center Data Parity Validation** entry point; it validates the parity matrix, legacy reference pin, public/private boundary, and private-store contracts without dispatching Full System Validation.
- `.github/workflows/reader-parity.yml` — historical reconciliation runs automatically only when historical migration inputs themselves change; it is no longer a general reader-development regression path.

### Implemented dependency-cone semantics

RunEngine stage modules map to the existing Iteration-aligned test that owns the stage plus its immediate predecessor/core dependency. Command Center UI and adapter changes map to Command Center contracts and a bounded snapshot-to-state integration. Reader runtime changes map to reader runtime/access checks without automatic historical replay. Approved-image packages retain their six-image/lock/digest integrity validation, and publication-adapter/manual-run changes retain representative adapter fixtures. Unknown material paths fail closed until the impact map is deliberately updated.

### Full System Validation operator contract

Full System Validation supports explicit manual selection of `all`, `python-comprehensive`, `reader-comprehensive`, or `command-center-comprehensive`, records the tested ref/SHA and reason, writes evidence under `evidence/full-system-validation/<run-id>/` in the workflow artifact, and does not mutate production.

The ordinary development workflow must not dispatch or invoke Full System Validation. The downstream Reader Parity Engineering Preview performs a lightweight change-impact check before its historical build/deploy work and skips that expensive path for unrelated main-branch changes; manual dispatch remains available.

## 17. Change log additions

| Date | Change |
|---|---|
| 2026-09-24 | Implemented centralized fail-closed change-impact routing, bounded Development/Integration Validation, narrowed automatic historical reader parity, change-impact-gated reader preview deployment, manual-only Full System Validation, and preserved approved-image/publication-adapter/manual-run validation in routed suites. |
| 2026-09-24 | Added dedicated Command Center Data Parity Validation as a bounded integration activity and manual/PR workflow; Full System Validation remains separate and is not auto-dispatched. |
