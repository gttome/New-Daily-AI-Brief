# Ready-to-Paste Iteration 14 Start Prompt

@GitHub Proceed with Iteration 14 of the New Daily AI Brief greenfield implementation in \`gttome/New-Daily-AI-Brief\`.

Use the current \`main\` branch as the source of truth. Before changing anything, verify the current \`main\` SHA, verify Iteration 13 is completely closed and passing, and read:

- \`docs/ITERATION14_HANDOFF_2026-09-21.md\`
- \`docs/ITERATION13_AFTER_ACTION_2026-09-21.md\`
- \`evidence/iteration13/synthetic-shadow-production-integration-admission-evidence.json\`
- \`docs/SCHEMA_VERSION_POLICY.md\`
- \`docs/ITERATION_START_PACKAGE_STANDARD.md\`

The Iteration 14 handoff is the controlling implementation specification.

Do not begin implementation if the Iteration 13 evidence reports a pending closure package or \`iteration14_ready=false\`. Use reconciled current repository records, not chat history or a remembered SHA, to establish the starting baseline.

Start from the merged Iteration 1–13 control plane and all locked artifacts. Preserve the existing lifecycle, state machine, canonical \`start_daily_brief(date, mode)\` entry point, lease/idempotency mechanism, content-addressed locks and digests, dependency invalidation, incident/recovery receipts, completion primitives, all locked Iterations 1–12 artifacts, and the locked Iteration 13 \`production-integration-admission\` artifact with its exact admission identity, exact direct binding to the Iteration 12 plan, exact transitive Iteration 11/10/9 identities, plan-graph/dry-run-assertion/rollback-boundary identities, current blocked classification, stable reason codes, explicit admission evidence bindings, separate admission-decision semantics, and fixed non-production authorization flags.

Implement Iteration 14 only: a deterministic, non-mutating production-integration execution preflight and authorization-envelope contract from the exact locked Iteration 13 admission artifact.

Build one versioned, content-addressed \`production-integration-execution-preflight\` artifact, or the equivalently named artifact required by the handoff, that directly binds the exact Iteration 13 admission artifact digest and \`admission_id\`, binds the Iteration 12 plan and all transitive upstream identities, and deterministically evaluates whether the admission is accompanied by a complete explicit repository-authoritative execution envelope suitable for a later separately authorized executor iteration.

The current repository configuration must remain \`blocked\` because the locked Iteration 13 admission remains blocked. Do not invent or infer executor identity, step enablement, target environment, verification approval, rollback authority, execution decision, cost approval, or any other missing execution identity from chat history or prior conversation.

A fully qualified synthetic \`authorization_ready\` admission may classify as logically \`execution_review_ready\` only when paired with a separate complete explicit synthetic execution envelope and separate execution-envelope decision. It must still carry \`synthetic_only=true\`, \`production_action_authorized=false\`, \`production_cutover_authorized=false\`, \`legacy_decommission_authorized=false\`, and \`production_publication=false\`. Every real integration-plan step must remain disabled in Iteration 14.

Add one bounded execution-preflight-only path through the existing canonical \`start_daily_brief(date, mode)\` owner, such as \`integration_execution_preflight_only=True\`. It must validate the locked Iteration 13 admission artifact and all bound upstream identities, evaluate one versioned execution-preflight policy/manifest, build or reuse one deterministic content-addressed execution-preflight artifact, keep lifecycle state \`Complete\`, set all production authorization flags false, perform no live action, and stop. Do not introduce a second orchestrator.

For a logically complete synthetic execution envelope, represent at minimum the exact Iteration 13 admission identity, exact executor contract/version identity, exact step-selection scope bound to the locked Iteration 12 ten-step graph, explicit per-step enablement with every real step disabled, dry-run assertion binding, rollback/restore binding, target-environment binding, pre-execution verification policy, stop/abort conditions, explicit no-cutover/no-decommission state, zero-incremental-cost guard, and a separate execution-envelope decision identity. Every input must bind explicit repository evidence.

Prove deterministic execution-preflight replay, exact binding to the Iteration 13 admission identity, exact plan and transitive upstream binding, stable classifications/reason codes, fail-closed stale/corrupted admission, fail-closed unsupported execution-preflight policy/schema versions, fail-closed changed admission identity, fail-closed changed execution-policy/manifest identity, proof that a synthetic authorization-ready admission alone is insufficient without a separate explicit execution envelope and decision, proof that no real integration step is enabled, targeted execution-preflight evaluation recovery, targeted final-artifact recovery, fresh-engine/no-chat resume, and zero reexecution of locked Iterations 1–13 work.

Do not implement or invoke a real production executor. Do not mutate the real/private Command Center Site. Do not implement the final Command Center UI, deploy to GitHub Pages or a public ChatGPT Site, change live/public URLs, perform real public-route verification, create/modify/enable/disable/run production schedules, change subscriber delivery, migrate legacy content, cut over production, route readers to greenfield, decommission legacy, publish to production, or modify/interfere with \`gttome/Daily-AI-Brief\`.

Do not add a separately billed OpenAI API, paid completion/storage API, paid deployment/hosting API, or other incremental paid production dependency. If any execution input would require such a dependency without explicit repository-authoritative zero-cost approval, it must remain blocked/fail-closed.

Do not stop for routine engineering decisions. Continue through implementation, testing, injected-failure recovery, deterministic replay, complete regression testing, PR/CI validation, merge, and post-merge \`main\` verification.

Iteration 14 is complete only after three consecutive synthetic/shadow execution-preflight-only runs independently satisfy the handoff exit gate with exactly one deterministic execution-preflight artifact, stable deterministic classification/reason codes, zero locked Iterations 1–13 reexecution, zero full-pipeline restart, no real integration step enabled, no real/private/public Site mutation, no production schedule action, no subscriber-delivery change, no migration/cutover/decommissioning action, and no production publication. Include dedicated proofs that the current blocked Iteration 13 admission cannot silently become \`execution_review_ready\` and that a synthetic \`authorization_ready\` admission does not become \`execution_review_ready\` without a separate explicit execution-envelope decision.

Merge only the exact candidate that passes the complete regression and Iteration 14 test suite. After merge, verify \`main\` CI again.

Finish by creating and merging all four required closure artifacts under \`docs/ITERATION_START_PACKAGE_STANDARD.md\`:

- \`docs/ITERATION14_AFTER_ACTION_2026-09-21.md\`;
- machine-readable Iteration 14 evidence under \`evidence/iteration14/\`;
- the authoritative Iteration 15 handoff;
- a separate ready-to-paste Iteration 15 start-prompt document.

Report the final \`main\` SHA, PRs, CI results, test counts, three-run exit-gate results, failure-recovery evidence, anti-rework metrics, all required closure-document paths, and whether Iteration 15 is ready to begin.
