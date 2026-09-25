# Public Command Center runtime and release notes

The September 25 user authorization supersedes owner-only application access. Application records and review notes are public; GitHub remains the sole production authority. No schedule, publisher, reader pipeline or old-system component was changed.

## Source reconciliation
GitHub baseline: `ffae7b31e3cd7f86428ab4811245cabe0eed7a9c`. npccs version 5: `3a20629262b8e581c11aeab818f3bce7ae7b18f3`. The v5 per-source Refresh adapter, reader-feed edition check, safe fallback and anti-regression behavior were retained and extended. No newer main changes existed at initial verification.

## Reproduction
`python scripts/test_command_center_runtime.py` builds and tests the worker using Node 24 and a real SQLite adapter for the D1 SQL interface. No npm dependency is required for the runtime tests. `records.json.gz` is the sanitized immutable migration input, not a fixture. `build.mjs` expands it and embeds the actual records in the worker bundle. The existing Sites project uses the same modules under `src/`; repository UI files remain at `site/command-center/`.

`python scripts/build_command_center_snapshot.py --main-sha <verified-sha>` invokes the same pure projection assembler. It does not run production or publish anything. The v1-to-v2 migration is deterministic, preserves its input, retains archived descriptors and rejects unknown schema versions. Both schema versions remain valid for historical evidence.

## Storage and public writes
Native Sites D1 binding `DB` holds proposals, Watchlist topics, comments, raw usage, imported snapshots, revision history, migration receipts, verified last-good states and rate buckets. Immutable historical evidence remains in the versioned deployment source. No browser storage is authoritative.

Public revision writes are same-origin JSON, limited to 8192 request bytes and 4096 note bytes. A fixed field allowlist rejects sensitive patterns and unknown fields. Each request has an idempotency key and base revision. SQL uniqueness and compare-and-swap protect concurrent updates. New history is append-only with truthful anonymous authorship. Rate limits are 10 writes per five minutes and 100 per day per daily-hashed network identifier; rate keys are never public. Read-back verifies every accepted revision. The shared-network fallback is deliberately bounded.

All eight proposal states are retained. New Applied transitions require a real GitHub commit in this repository, a changed docs/books/manuscripts path, and the exact proposal ID in the commit message. If a proposal specifies a target path, it must agree. Imported historical Applied states are preserved even when evidence is incomplete. The current book manuscripts have not been mapped into this repository; no anonymous note can claim a real book change.

Only fixed review operations and non-destructive imported-comment retention verification accept public writes. No dispatch, repair, publication, Force Replace, arbitrary import, SQL or delete endpoint exists. Retention verification is explicitly scoped to imported comments; existing native-reader cleanup remains outside this application's authority.

## Data provenance and limitations
The September 24 operational edition is recovered from canonical GitHub workflow run 36051784007, artifact 10829999743, source SHA `4a0faf7bc3637bab7d27ee95bfa0dc542e0f958c`. Its build-locked state does not prove unrecorded later canonical stages. Dated legacy measurements retain their boundaries; measured zero and missing values differ. Baselines deduplicate attempt/boundary/metric/unit and exclude conflicting observations. Native reader signals are fetched separately from historical aggregates and are never added to overlapping legacy totals.

Nine truncated input records were excluded (two evaluation exports, two usage payloads, five snapshots); two full evaluation receipts were recovered independently from pinned old Site source. Inaccessible payloads are not claimed migrated. Future canonical artifacts are not automatically accessible through the public GitHub artifact-download API; the runtime fails stale/partial rather than inventing a newer projection. Native-reader comments and audience/subscription events have no compatible public export; this release does not change ndaib to create one.

## Validation boundaries
Contract mapping, deployed implementation and live acceptance are separate. Native deployment success does not prove anonymous persistence. Local SQL tests do not prove live D1 writes. See the 69-row functional ledger and final report for actual execution evidence and unresolved acceptance.

## Rollback
Prior npccs version 5 and GitHub baseline above are rollback anchors. Re-deploying v5 does not delete the new D1 records. Its access model is obsolete; restore private access if an emergency rollback uses that owner-only implementation. Never drop the append-only tables to roll back UI code. No old system or reader rollback is necessary because neither was modified.
