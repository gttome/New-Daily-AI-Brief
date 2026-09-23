# Iteration 32 Closure Directive — Iteration 33 Testing-System Redesign

Prepared September 23, 2026.

This directive records the owner's required next-iteration scope. It is documentation-only and does not change runtime behavior, deployment semantics, production routing, or any locked Iterations 1–32 architecture.

## Mandatory Iteration 32 closure requirement

The Iteration 32 after-action report, machine-readable closure evidence, Iteration 33 handoff, and Iteration 33 standalone start prompt MUST state that:

**Iteration 33 is dedicated completely to redesigning the greenfield testing/CI system before further feature-development iterations proceed.**

The current test system has made normal development impractical. Recent equivalent Greenfield Contracts runs have taken roughly 50–80 minutes, and the current workflow duplicates expensive verification by running heavy targeted historical/Iteration tests and then running the same tests again through full test discovery.

## Iteration 33 required redesign objectives

Iteration 33 must redesign the testing system while preserving all safety, fail-closed, recovery, deterministic-evidence, protected-main, and required-check guarantees.

At minimum, the redesign must address:

1. duplicate execution of heavy historical/Iteration tests across targeted and full-discovery phases;
2. excessive 50–80 minute routine full-suite wall-clock time;
3. repeated verification of runtime trees already proven by an exact-head full Greenfield Contracts run;
4. post-merge verification strategy for an unchanged, exact tree already tested on the PR head;
5. test layering and selection so small changes run only the coverage they require;
6. deterministic reuse of exact-head results where repository tree identity proves equivalence;
7. caching or other safe reuse where it materially reduces repeated computation;
8. bounded metadata/documentation validation that never invokes runtime/recovery suites unnecessarily;
9. deployment gating that can safely use proven exact-tree verification without waiting for redundant historical re-execution;
10. explicit cancellation/retirement handling for superseded runs when the available GitHub execution surface permits it;
11. durable timing telemetry by test phase so regressions in test runtime are immediately visible;
12. hard maximum runtime targets and fail-fast behavior for routine development checks.

## Required evidence for Iteration 33

Before changing the testing architecture, Iteration 33 must baseline:
- current workflow topology;
- test inventory and dependency graph;
- targeted-step runtime;
- full-discovery runtime;
- duplicated test execution;
- PR exact-head runtime;
- post-merge runtime;
- deployment wait attributable to CI;
- historical 50–80 minute runs relevant to the redesign.

The redesigned system must demonstrate materially lower development latency without weakening:
- the required **Greenfield Contracts** check identity;
- executable/runtime/schema/fixture/workflow regression coverage;
- recovery and replay testing;
- fail-closed behavior;
- deterministic evidence;
- protected-main controls;
- production isolation.

## Sequencing

Do not begin Iteration 33 until Iteration 32 owner hands-on testing is completed and the owner explicitly authorizes Iteration 32 closure/continuation. Once authorized, the Iteration 32 closure package must carry this directive forward unchanged in substance.
