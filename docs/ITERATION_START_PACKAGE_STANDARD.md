# New Daily AI Brief — Iteration Start Package Standard
## Required for Every Iteration Beginning with Iteration 4

This document defines the mandatory new-chat handoff package for every future greenfield implementation iteration.

## Purpose

Each iteration must be independently restartable in a fresh ChatGPT chat without relying on prior chat context. Repository records, not conversation history, are the source of truth.

## Mandatory closure package

An iteration is not considered operationally closed until the repository contains all of the following:

1. **After-action report**
   - records implemented scope;
   - final implementation and closure SHAs;
   - PR numbers;
   - PR and post-merge CI results;
   - test counts;
   - exit-gate results;
   - recovery evidence;
   - anti-rework metrics;
   - deferred scope.

2. **Machine-readable evidence**
   - deterministic exit-gate evidence;
   - recovery evidence;
   - replay/digest evidence;
   - CI and repository-closure identities.

3. **Authoritative next-iteration handoff**
   - exact starting baseline;
   - controlling scope;
   - preserved architecture/contracts;
   - explicit non-scope;
   - required tests and recovery proof;
   - exit gate;
   - closure requirements.

4. **Standalone next-iteration start prompt**
   - a separate `.md` file containing a complete ready-to-paste prompt for a new ChatGPT chat;
   - the prompt must explicitly invoke `@GitHub`;
   - it must instruct the new chat to use current `main` as source of truth;
   - it must name the authoritative handoff, prior after-action, machine-readable evidence, and schema/contract records that must be read before changes;
   - it must preserve the existing lifecycle/orchestrator and explicitly prohibit rework of completed prior iterations;
   - it must restate paid-dependency restrictions and production-repository protections;
   - it must require implementation through PR/CI/merge/post-merge verification;
   - it must require creation of the next handoff **and next standalone start prompt**.

## Naming convention

For iteration `N`:

- `docs/ITERATIONN_AFTER_ACTION_YYYY-MM-DD.md`
- `evidence/iterationN/<authoritative-evidence-file>.json`
- `docs/ITERATION(N+1)_HANDOFF_YYYY-MM-DD.md`
- `docs/ITERATION(N+1)_START_PROMPT_YYYY-MM-DD.md`

## New-chat startup rule

The user should be able to start the next iteration by opening a new chat and pasting only the contents of the standalone start-prompt file.

The receiving chat must then retrieve the named repository records itself and verify the current `main` SHA and CI state before changing anything.

## No-chat dependency rule

Do not make a future iteration dependent on:
- hidden prior-chat reasoning;
- attachments that are not also represented by authoritative repository records when required for implementation;
- unstated decisions from a previous chat;
- manually remembered SHAs or CI state.

If a decision is required to continue safely in the next iteration, record it in the repository handoff before closing the current iteration.

## Completion rule

Starting with Iteration 4, the phrase **"ready for the next iteration"** means all four closure artifacts above exist on verified `main`, and the standalone next-iteration prompt can be pasted into a new chat without additional reconstruction.
