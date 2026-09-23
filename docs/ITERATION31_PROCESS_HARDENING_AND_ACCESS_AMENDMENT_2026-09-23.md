# New Daily AI Brief — Iteration 31 Process-Hardening and User-Access Amendment
## Superseding process requirements for Iteration 31 and fixed Iteration 32 access milestone

Prepared September 23, 2026. Repository: `gttome/New-Daily-AI-Brief`.

This amendment does **not** reopen or alter Iteration 30 closure. Iteration 30 remains complete. It supplements the authoritative Iteration 31 handoff with process requirements intended to prevent repeated rework, unnecessary long-running closure verification, and moving user-access targets.

## Process-hardening prelude — required before Iteration 31 implementation

Perform these changes as an unnumbered process-hardening prelude on the Iteration 31 implementation branch. Do not create another numbered iteration for this work and do not rebuild or reexecute completed Iterations 1–30.

1. **Path-aware CI**
   - Preserve the repository's required CI status/check contract.
   - Runtime, schema, fixture, test, workflow, or other executable/contract changes must still receive the complete Greenfield Contracts regression suite.
   - Documentation/evidence-only closure or reconciliation changes must use a bounded metadata/closure validation path instead of rerunning the entire historical runtime/recovery suite when runtime code, schemas, fixtures, tests, and workflow logic are unchanged.
   - The bounded closure path must at minimum validate syntax/JSON, required closure files, internal references, repository-closure flags, next-iteration readiness flags, and immutable implementation/CI identities.

2. **Durable iteration progress state**
   - Record an authoritative machine-readable iteration progress/checkpoint record in the repository.
   - The record must identify the iteration, phase, exact branch/head, completed gates, active gate, CI run identities, closure state, and next permissible action.
   - Chat history must never be required to determine where to resume.

3. **Idempotent retry/resume**
   - A retry must inspect current `main`, open/merged PRs, current candidate SHA, CI state, closure artifacts, and the progress record before creating or rerunning anything.
   - Completed work must be reused.
   - Never create a duplicate PR, duplicate closure package, duplicate CI run, or rebuild a locked prior artifact solely because a chat restarted or the user said “retry”.
   - If an existing exact-head CI run is queued/in-progress, continue from it rather than starting another run.

4. **Closure-state automation**
   - Make closure progression explicit: implementation verified → closure package → closure verification → reconciliation → final main verification → next iteration ready.
   - Persist each transition so the next chat can continue from the last durable boundary.
   - Closure/reconciliation changes must remain metadata-only and must not modify runtime semantics.

5. **Performance evidence**
   - Record elapsed CI time for the implementation, closure, and reconciliation paths.
   - Demonstrate that documentation/evidence-only closure work no longer incurs the full historical runtime/recovery suite unless an executable or contract-bearing file changed.
   - Do not weaken runtime safety coverage to achieve this.

## Iteration 31 technical scope

After the process-hardening prelude is verified, implement only the Iteration 31 synthetic executor-binding authorization-package-readiness authorization-package gate defined by `docs/ITERATION31_HANDOFF_2026-09-21.md`.

The amendment does not authorize production executor use, credentials, target contact, deployment, publication, schedule changes, cutover, decommissioning, or changes to `gttome/Daily-AI-Brief`.

## Fixed Iteration 32 user-access milestone

**Iteration 32 is the fixed user-access milestone and must not be deferred to a later iteration.**

The Iteration 31 closure package must create an Iteration 32 handoff and standalone start prompt whose mandatory exit gate requires a user-accessible greenfield system for meaningful testing, including:

- a functioning greenfield Daily Generative AI Brief reader site;
- a functioning private greenfield Command Center;
- real URLs that the owner can open on desktop and phone;
- representative end-to-end brief data flowing through the greenfield architecture;
- usable reader navigation, archive, Watchlist, article/media surfaces, and required ratings/sharing surfaces needed for acceptance testing;
- observable run/QA/readiness state in the private Command Center;
- coexistence with the current production Daily AI Brief so the existing system is not endangered;
- an owner-facing acceptance checklist.

Iteration 32 may remain pre-cutover/shadow and must preserve safety boundaries, but it **may not** be closed solely by another synthetic authorization/readiness gate. It is not complete until the owner has working URLs for the reader site and Command Center and those surfaces pass the documented access/acceptance checks.

No Iteration 33 or later may be inserted as a prerequisite for first owner access to the working greenfield system.

## Precedence

Where this amendment conflicts with the old standalone Iteration 31 start prompt, this amendment and the superseding Iteration 31 start prompt dated September 23, 2026 control. The existing Iteration 31 handoff continues to control the bounded Iteration 31 technical gate except where this amendment adds process-hardening and the fixed Iteration 32 access milestone.
