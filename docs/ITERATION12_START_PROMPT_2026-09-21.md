@GitHub Proceed with Iteration 12 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 11 is completely closed and passing, and read:

- `docs/ITERATION12_HANDOFF_2026-09-21.md`
- `docs/ITERATION11_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration11/synthetic-shadow-production-integration-preflight-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 12 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 11 evidence reports a pending closure package or `iteration12_ready=false`. Use the reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–11 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, all locked Iterations 1–10 artifacts, and the locked Iteration 11 `production-integration-preflight` artifact with its exact preflight identity, exact binding to the Iteration 10 readiness artifact/assessment, complete ten-prerequisite resolution inventory, stable resolution reason codes, and explicit non-production authorization semantics.

Implement Iteration 12 only: a deterministic, non-mutating production-integration plan compiler and dry-run contract-validation layer from the locked Iteration 11 preflight decision.

Build one versioned, content-addressed `production-integration-plan` artifact, or equivalently named artifact if the handoff requires it, that binds the exact Iteration 11 preflight identity and deterministically maps repository-authoritative resolved prerequisite evidence into the future integration steps, dependencies, dry-run assertions, rollback boundaries, target/adapter/schedule/verification references, and cost guards that would be required by a later controlled integration iteration.

The current repository configuration must remain `blocked` because the locked Iteration 11 preflight remains unresolved for eight production prerequisites. Do not invent or infer adapter identity, publication target, public deployment/verification target, private Command Center target, production schedule identity/cadence, migration/cutover approval, rollback identity, cost approval, or any other missing integration identity from chat history or prior conversation.

A fully qualified synthetic Iteration 11 preflight may compile as logically `planned` only to prove plan-compiler logic. It must still carry `synthetic_only=true`, `production_action_authorized=false`, `production_cutover_authorized=false`, `legacy_decommission_authorized=false`, and `production_publication=false`.

Add a bounded plan-only path through the existing canonical `start_daily_brief(date, mode)` owner, such as `integration_plan_only=True`. It must validate the locked Iteration 11 preflight artifact and all bound upstream identities, evaluate one versioned plan policy, build or reuse one deterministic content-addressed plan artifact, keep lifecycle state `Complete`, set all production authorization flags false, perform no live action, and stop. Do not introduce a second orchestrator.

For a logically complete synthetic plan, represent at minimum the discovery adapter binding, publication path/target, public deployment binding, public verification mechanism, private Command Center projection/privacy binding, production schedule identities/cadences, subscriber-delivery policy enforcement, migration prerequisites with explicit no-cutover/no-decommission state, rollback/recovery boundary and restore identity, and zero-incremental-cost guard. Every plan step must bind explicit repository evidence and carry predecessor/dependency information, dry-run assertions, a rollback/failure boundary, and `production_action_authorized=false`.

Prove deterministic plan replay, exact binding to the Iteration 11 preflight identity, complete stable classifications/reason codes, fail-closed stale/corrupted preflight, fail-closed unsupported plan policy/schema versions, fail-closed changed preflight identity, fail-closed changed plan-policy identity, targeted plan-compilation recovery, targeted final-plan-artifact recovery, fresh-engine/no-chat resume, and zero reexecution of locked Iterations 1–11 work.

Do not mutate the real/private Command Center Site. Do not implement the final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to the greenfield system, decommission the legacy system, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. If any plan input would require such a dependency without explicit repository-authoritative approval, it must remain blocked/fail-closed.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 12 is complete only after three consecutive synthetic/shadow plan-only runs independently satisfy the handoff exit gate with exactly one deterministic plan artifact, stable deterministic classification/reason codes, zero locked Iterations 1–11 reexecution, zero full-pipeline restart, no real/private/public Site mutation, no production schedule action, no migration/cutover/decommissioning action, and no production publication. Include a dedicated proof that the current unresolved Iteration 11 preflight cannot silently become `planned`.

Merge only the exact candidate that passes the complete regression and Iteration 12 test suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION12_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 12 evidence under `evidence/iteration12/`;
- the authoritative Iteration 13 handoff;
- a separate ready-to-paste Iteration 13 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 13 is ready to begin.
