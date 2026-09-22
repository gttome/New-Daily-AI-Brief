# Ready-to-Paste Iteration 13 Start Prompt

@GitHub Proceed with Iteration 13 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 12 is completely closed and passing, and read:

- `docs/ITERATION13_HANDOFF_2026-09-21.md`
- `docs/ITERATION12_AFTER_ACTION_2026-09-21.md`
- `evidence/iteration12/synthetic-shadow-production-integration-plan-evidence.json`
- `docs/SCHEMA_VERSION_POLICY.md`
- `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 13 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 12 evidence reports a pending closure package or `iteration13_ready=false`. Use reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–12 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, all locked Iterations 1–11 artifacts, and the locked Iteration 12 `production-integration-plan` artifact with its exact plan identity, exact binding to the Iteration 11 preflight and transitive Iteration 10/9 identities, ten-step dependency graph, dry-run assertion set, rollback boundaries, current blocked classification, stable reason codes, and explicit non-production authorization semantics.

Implement Iteration 13 only: a deterministic, non-mutating production-integration admission gate and execution-authorization-readiness contract from the locked Iteration 12 plan.

Build one versioned, content-addressed `production-integration-admission` artifact, or equivalently named artifact if the handoff requires it, that binds the exact Iteration 12 plan identity and deterministically evaluates whether the plan is accompanied by complete, explicit, repository-authoritative admission evidence suitable for a later controlled execution iteration.

The current repository configuration must remain `blocked` because the locked Iteration 12 plan remains blocked. Do not invent or infer adapter identity, publication target, public deployment/verification target, private Command Center target, production schedule identity/cadence, migration/cutover approval, rollback identity, cost approval, admission decision, or any other missing production identity from chat history or prior conversation.

A fully qualified synthetic planned configuration may classify as logically `authorization_ready` only when paired with a separate explicit synthetic admission package. It must still carry `synthetic_only=true`, `production_action_authorized=false`, `production_cutover_authorized=false`, `legacy_decommission_authorized=false`, and `production_publication=false`.

Add one bounded admission-only path through the existing canonical `start_daily_brief(date, mode)` owner, such as `integration_admission_only=True`. It must validate the locked Iteration 12 plan artifact and all bound upstream identities, evaluate one versioned admission policy/manifest, build or reuse one deterministic content-addressed admission artifact, keep lifecycle state `Complete`, set all production authorization flags false, perform no live action, and stop. Do not introduce a second orchestrator.

For a logically complete synthetic admission package, represent at minimum the exact plan identity, discovery adapter, publication path/target, public deployment and verification mechanism, private Command Center projection/privacy binding, production schedule identities/cadences, subscriber-delivery policy, migration prerequisites with explicit no-cutover/no-decommission state, rollback/restore identity, zero-incremental-cost guard, and a separate admission decision identity. Every admitted input must bind explicit repository evidence.

Prove deterministic admission replay, exact binding to the Iteration 12 plan identity, stable classifications/reason codes, fail-closed stale/corrupted plan, fail-closed unsupported admission policy/schema versions, fail-closed changed plan identity, fail-closed changed admission-policy/manifest identity, proof that a synthetic planned plan alone is insufficient without separate admission evidence, targeted admission-evaluation recovery, targeted final-admission-artifact recovery, fresh-engine/no-chat resume, and zero reexecution of locked Iterations 1–12 work.

Do not mutate the real/private Command Center Site. Do not implement the final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. If any admission input would require such a dependency without explicit repository-authoritative approval, it must remain blocked/fail-closed.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 13 is complete only after three consecutive synthetic/shadow admission-only runs independently satisfy the handoff exit gate with exactly one deterministic admission artifact, stable deterministic classification/reason codes, zero locked Iterations 1–12 reexecution, zero full-pipeline restart, no real/private/public Site mutation, no production schedule action, no migration/cutover/decommissioning action, and no production publication. Include dedicated proofs that the current blocked Iteration 12 plan cannot silently become `authorization_ready` and that a synthetic planned plan does not become `authorization_ready` without a separate explicit admission decision.

Merge only the exact candidate that passes the complete regression and Iteration 13 test suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

- `docs/ITERATION13_AFTER_ACTION_2026-09-21.md`;
- machine-readable Iteration 13 evidence under `evidence/iteration13/`;
- the authoritative Iteration 14 handoff;
- a separate ready-to-paste Iteration 14 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 14 is ready to begin.
