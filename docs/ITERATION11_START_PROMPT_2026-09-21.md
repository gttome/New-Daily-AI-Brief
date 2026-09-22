@GitHub Proceed with Iteration 11 of the New Daily AI Brief greenfield implementation in `gttome/New-Daily-AI-Brief`.

Use the current `main` branch as the source of truth. Before changing anything, verify the current `main` SHA, verify Iteration 10 is completely closed and passing, and read:

* `docs/ITERATION11_HANDOFF_2026-09-21.md`
* `docs/ITERATION10_AFTER_ACTION_2026-09-21.md`
* `evidence/iteration10/synthetic-shadow-production-readiness-evidence.json`
* `docs/SCHEMA_VERSION_POLICY.md`
* `docs/ITERATION_START_PACKAGE_STANDARD.md`

The Iteration 11 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 10 evidence reports a pending closure package or `iteration11_ready=false`. Use the reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–10 control plane and locked artifacts. Preserve the existing lifecycle, state machine, canonical `start_daily_brief(date, mode)` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, all locked Iterations 1–9 artifacts, the locked Iteration 9 final completion artifact/receipt with final state `Complete` and status `complete_locked`, and the locked Iteration 10 `readiness-admission` artifact with its exact readiness identity, ten-prerequisite inventory, stable reason codes, and explicit non-production authorization semantics.

Implement Iteration 11 only: a deterministic, non-mutating production-integration preflight and prerequisite-resolution layer from the locked Iteration 10 readiness decision.

Build one versioned, content-addressed `production-integration-preflight` artifact, or equivalently named artifact if the handoff requires it, that binds the exact Iteration 10 readiness identity and converts every readiness prerequisite/result into an explicit repository-authoritative resolution requirement. The artifact must identify what evidence is required to resolve each blocker, bind any evidence that actually exists, classify each prerequisite as resolved/unresolved/invalid with stable reason codes, and produce one deterministic overall preflight classification.

Add a bounded preflight-only path through the existing canonical `start_daily_brief(date, mode)` owner, such as `integration_preflight_only=True`. It must validate the locked Iteration 10 readiness artifact and all bound upstream identities, evaluate one versioned resolution policy/manifest, build or reuse one deterministic content-addressed preflight artifact, keep lifecycle state `Complete`, set `production_action_authorized=false`, perform no live action, and stop. Do not introduce a second orchestrator.

Use synthetic/shadow fixtures only. Prove both policy outcomes:

* the current repository configuration must remain `unresolved` for every blocker that lacks explicit repository-authoritative resolution evidence; and
* a fully qualified synthetic resolution manifest may classify as logically `qualified` only to prove evaluator logic and must still carry `synthetic_only=true`, `production_action_authorized=false`, `production_cutover_authorized=false`, `legacy_decommission_authorized=false`, and `production_publication=false`.

Never infer approval, capability, adapter identity, target identity, schedule authority, rollback identity, cost approval, or cutover authority from chat history. Missing evidence remains unresolved or fail-closed.

Prove deterministic preflight replay, exact binding to the Iteration 10 readiness identity, complete stable resolution reason codes, fail-closed stale/corrupted readiness, fail-closed unsupported policy/schema versions, fail-closed changed readiness identity, fail-closed changed resolution-manifest identity, targeted resolution-evaluation recovery, targeted final-preflight-artifact recovery, fresh-engine/no-chat resume, and zero reexecution of locked Iterations 1–10 work.

Do not mutate the real/private Command Center Site. Do not implement the final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to the greenfield system, decommission the legacy system, publish to production, or modify/interfere with `gttome/Daily-AI-Brief`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. If any prerequisite would require such a dependency without explicit repository-authoritative approval, it must remain unresolved/blocked.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge `main` verification.

Iteration 11 is complete only after three consecutive synthetic/shadow preflight-only runs independently satisfy the handoff exit gate with exactly one deterministic preflight artifact, stable deterministic classification/reason codes, zero locked Iterations 1–10 reexecution, zero full-pipeline restart, no real/private/public Site mutation, no production schedule action, no migration/cutover/decommissioning action, and no production publication. Include a dedicated proof that the currently unresolved production prerequisites do not silently become qualified.

Merge only the exact candidate that passes the complete regression and Iteration 11 test suite. After merge, verify `main` CI again.

Finish by creating and merging all four required closure artifacts under `docs/ITERATION_START_PACKAGE_STANDARD.md`:

* `docs/ITERATION11_AFTER_ACTION_2026-09-21.md`;
* machine-readable Iteration 11 evidence under `evidence/iteration11/`;
* the authoritative Iteration 12 handoff;
* a separate ready-to-paste Iteration 12 start-prompt document.

Report the final `main` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 12 is ready to begin.
