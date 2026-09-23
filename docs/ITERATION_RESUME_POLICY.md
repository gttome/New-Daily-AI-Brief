# Iteration Retry, Resume, and Closure Progress Policy

This policy implements the Iteration 31 process-hardening amendment without creating another numbered iteration.

## Source of truth

Repository state is authoritative. A fresh chat must inspect current `main`, the durable iteration progress record, open or merged pull requests, exact candidate SHAs, existing CI runs for those SHAs, merge identities, and required closure artifacts before creating or rerunning work.

For Iteration 31 the durable record is `evidence/iteration31/progress.json`.

## Idempotent retry

A user message such as “retry”, “continue”, or “status” means resume from the last repository checkpoint. It does not authorize recreation of completed work.

- Reuse an existing PR for the same active gate.
- Reuse an exact-head CI run that is queued, in progress, or already successful.
- Reuse merged commits and locked artifacts.
- Reuse an existing closure package and reconciliation records.
- Never rebuild Iterations 1–30 because a chat restarted.
- Never create a duplicate PR or duplicate CI run solely to recover chat state.

## Closure state machine

The durable closure sequence is:

`implementation_verified → closure_package → closure_verification → reconciliation → final_main_verification → complete`.

Each transition is persisted in the iteration progress record. The record identifies the exact checkpoint head, known CI identities, completed gates, active gate, closure state, and the next permissible action.

## CI scope

The required workflow/check remains **Greenfield Contracts**.

Executable or contract-bearing changes—including runtime code, schemas, fixtures, tests, scripts, and workflow logic—run compile plus the complete historical regression/recovery suite.

Changes limited to `docs/**` and `evidence/**` use the bounded closure metadata validator. That validator parses JSON, validates repository references, required closure paths, closure/readiness consistency, durable progress fields, and protects immutable implementation evidence against metadata-only rewrites.

This optimization does not reduce runtime safety coverage: any executable or contract-bearing path forces the full suite.
