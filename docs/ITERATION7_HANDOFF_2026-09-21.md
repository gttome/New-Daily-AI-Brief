# New Daily AI Brief — Iteration 7 Handoff
## Deterministic Post-Publication Book-Change Evaluation
### Prepared September 21, 2026

## Activation condition

Iteration 7 is activated only after Iteration 6 operational closure is complete under `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Before changing anything, verify current `main` and read:

- `docs/ITERATION6_AFTER_ACTION_2026-09-21.md`;
- `evidence/iteration6/synthetic-shadow-release-evidence.json`;
- `docs/SCHEMA_VERSION_POLICY.md`;
- `docs/ITERATION_START_PACKAGE_STANDARD.md`.

The current repository records, not chat history or a manually remembered SHA, are authoritative.

Do not begin implementation if the Iteration 6 evidence still reports a pending closure package or `iteration7_ready=false`.

## Validated implementation baseline

Iteration 6 implementation was merged through PR **#14**.

Exact passing implementation candidate:

`664fe29bc5aeed30bd708cd4029cd7a8b92223fb`

PR CI run **35677602434** passed the complete **67/67** regression suite.

Implementation merge SHA:

`36b974dee16c20224af2cfaaa87c2640953d8b5b`

Post-merge `main` run **35677728380** passed **67/67** tests.

The final closure-package identities must be taken from the reconciled Iteration 6 after-action/evidence on then-current `main`.

## Starting point

Iterations 1–6 provide one recoverable greenfield control plane with:

- canonical `start_daily_brief(date, mode)`;
- durable lifecycle/state machine and lease/idempotency;
- content-addressed locks/digests and descendant-only invalidation;
- incident/recovery receipts and no-chat resume;
- deterministic exact 2/2/2 six-story edition with exactly one reusable Agent Skills story;
- exactly two verified videos and two verified podcasts;
- date-current Watchlist delta;
- exactly six Professional Series bridge decisions;
- exactly six accepted story images;
- `five-star-v1` rating contract;
- passing locked Iteration 4 publication bundle;
- locked Iteration 5 reader-render artifact;
- locked Iteration 5 route/render manifest with exactly 11 outputs;
- locked Iteration 6 release package;
- locked Iteration 6 shadow deployment receipt;
- locked Iteration 6 offline live-verification receipt with `verification_scope=shadow_offline`;
- final bounded Iteration 6 lifecycle state `LiveVerified`;
- production deployment adapters still fail closed;
- no public deployment, Command Center projection, migration, cutover, or legacy-system change.

All locked Iteration 1–6 artifacts are immutable upstream input for Iteration 7.

## Mission

Implement the next bounded slice only: **deterministic synthetic/shadow post-publication evaluation of every included brief item for Generative AI Professional Series book-change proposals**.

Iteration 7 may exercise:

`LiveVerified → PostPublicationEvaluation`

in synthetic/shadow mode only.

It must create and lock the post-publication evaluation artifact and then **stop at `PostPublicationEvaluation`** with a bounded completion status. It must not transition to `OperationsReconciled`, project the Command Center, or create final completion.

Do not introduce another lifecycle owner or bypass `start_daily_brief(date, mode)`.

## A. Post-publication evaluation contract

Create a versioned deterministic evaluation contract that requires evaluation of every included published item represented by the locked release chain:

- all six articles/stories in locked presentation order;
- both verified videos;
- both verified podcasts.

Exactly **10 included items** must therefore receive an explicit evaluation disposition.

For each item, persist enough deterministic evidence to distinguish:

- evaluated and proposal warranted;
- evaluated and no material proposal warranted;
- unavailable/invalid input;
- not evaluated.

`0 proposals` is valid only when all 10 included items were explicitly evaluated and no material proposal was warranted. Missing evaluation must never be interpreted as zero.

## B. Input binding

The evaluation must fail closed unless all required Iteration 6 release identities are locked, valid, and mutually consistent.

At minimum bind evaluation semantic identity to:

- locked publication-bundle digest;
- locked route-manifest digest;
- locked release-package digest;
- locked shadow-deployment digest/identity;
- locked passing live-verification digest;
- evaluation contract version.

The live-verification receipt must have:

- `verification_scope=shadow_offline`;
- `result=passed`;
- `shadow_only=true`;
- `production_authorized=false`.

Do not evaluate from an unverified or stale release.

## C. Deterministic synthetic/shadow evaluator

Use fixture-backed synthetic/shadow evaluation first.

Requirements:

- deterministic item-level decisions for identical locked inputs;
- no separately billed OpenAI API;
- no paid external evaluation service;
- no dependence on chat/session state;
- production evaluator remains fail closed until a separately approved zero-incremental-cost production path exists;
- volatile elapsed time/timestamps do not affect semantic artifact identity.

The artifact should include:

- evaluation contract version;
- edition date;
- exact ordered evaluated item IDs/types;
- item-level dispositions and rationale/evidence identifiers;
- proposal records when warranted;
- proposal count;
- explicit all-items-evaluated boolean;
- a human-readable result string that distinguishes true zero from missingness;
- all bound upstream release identities.

## D. Bounded lifecycle execution

Add a bounded Iteration 7 execution path through the canonical entry point that:

1. requires the run to be at `LiveVerified` (or recovering from the Iteration 7 boundary);
2. requires the locked passing Iteration 6 release/verification chain;
3. reuses all locked Iteration 1–6 artifacts;
4. transitions to `PostPublicationEvaluation`;
5. evaluates/reuses exactly the 10 included items;
6. locks one deterministic post-publication book-change evaluation artifact;
7. stops in `PostPublicationEvaluation`;
8. records a bounded status such as `post_publication_evaluation_locked`.

Do not project to or reconcile the Command Center in Iteration 7.

## E. Recovery requirements

Inject failures proving targeted recovery for at least:

- one individual included-item evaluation after earlier item decisions are durable;
- final evaluation-artifact assembly/validation after all item decisions are durable.

A fresh engine instance must resume without chat/session context.

Required anti-rework result:

- zero discovery reexecution;
- zero editorial reexecution;
- zero media reexecution;
- zero Watchlist reexecution;
- zero bridge reexecution;
- zero accepted-image rework;
- zero publication-bundle rebuild;
- zero reader-render rebuild;
- zero route-manifest rebuild;
- zero release-package rebuild;
- zero shadow-deployment rewrite/redeployment;
- zero live-verification rerun when its locked receipt is valid;
- zero already evaluated unrelated item rewrite during targeted recovery;
- zero full-pipeline restart.

## F. Fail-closed requirements

Fail closed if:

- any required Iteration 1–6 lock is missing, invalidated, stale, corrupted, or schema-incompatible;
- route/release/deployment/verification identities do not bind consistently;
- live verification is absent or not passing;
- verification scope is not `shadow_offline`;
- required item membership differs from the locked six articles/two videos/two podcasts;
- an included item lacks an explicit evaluation disposition;
- proposal count differs from the actual proposal records;
- `0 proposals` is asserted while any included item is unevaluated/unavailable;
- a cached item decision or final evaluation artifact is corrupted;
- a production evaluation adapter is requested without approved zero-incremental-cost authorization.

## G. Telemetry

Persist bounded Iteration 7 telemetry for:

- item evaluation attempts/retries/cache reuse;
- item evaluation failures;
- evaluation-artifact attempts/reuse;
- validation checks/failures by invariant;
- elapsed time;
- anti-rework counters.

Volatile telemetry must remain outside semantic artifact identity.

## Explicit non-scope

Iteration 7 must **not**:

- deploy to GitHub Pages;
- deploy to or mutate a public ChatGPT Site;
- change any live/public URL;
- perform real public-route verification;
- project to the private Command Center;
- implement Command Center UI;
- transition to `OperationsReconciled` or `Complete`;
- create or modify production schedules;
- change subscriber delivery;
- migrate legacy historical content;
- cut over production;
- decommission the legacy system;
- modify or interrupt `gttome/Daily-AI-Brief`;
- add a separately billed OpenAI API, paid evaluation API, paid deployment/hosting API, or other incremental paid production dependency.

## Required proof

At minimum prove:

1. exact 10-item evaluation membership: 6 articles + 2 videos + 2 podcasts;
2. every item receives an explicit disposition;
3. deterministic evaluation replay for identical locked inputs;
4. true zero-proposal result is distinguishable from missing/incomplete evaluation;
5. proposal count exactly matches proposal records;
6. evaluation identity binds the complete locked Iteration 6 release/verification chain;
7. fail-closed stale/corrupted live-verification receipt;
8. fail-closed incomplete item evaluation;
9. fail-closed corrupted cached item evaluation;
10. targeted one-item recovery;
11. targeted final evaluation-artifact recovery;
12. fresh-engine/no-chat resume;
13. zero reexecution of locked Iteration 1–6 work;
14. no Command Center projection or final completion;
15. no public deployment, URL mutation, schedules, migration, cutover, or production publication.

## Exit gate

Iteration 7 is complete only after **three consecutive synthetic/shadow evaluation-only runs**, each beginning from a valid locked Iteration 6 `LiveVerified` release chain, independently produce without manual intervention:

- exactly 10 explicit item evaluations;
- one deterministic locked post-publication evaluation artifact;
- internally consistent proposal records/count;
- correct zero-versus-missing semantics;
- identical semantic evaluation identity for identical locked inputs;
- zero unrelated locked-stage reexecution;
- final lifecycle state `PostPublicationEvaluation`;
- bounded completion status `post_publication_evaluation_locked`;
- no `OperationsReconciled` transition;
- no Command Center projection;
- no final completion artifact;
- no public deployment/live-route mutation;
- no production publication.

Merge only the exact candidate that passes the complete regression + Iteration 7 suite. After merge, verify `main` CI again.

## Required closure records

Iteration 7 must follow `docs/ITERATION_START_PACKAGE_STANDARD.md`.

Finish by creating and merging all four required closure artifacts:

- `docs/ITERATION7_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 7 evidence under `evidence/iteration7/`;
- authoritative `docs/ITERATION8_HANDOFF_2026-09-21.md`;
- standalone ready-to-paste `docs/ITERATION8_START_PROMPT_2026-09-21.md`.

Do not report Iteration 8 as ready until all four artifacts are present on verified `main`.
