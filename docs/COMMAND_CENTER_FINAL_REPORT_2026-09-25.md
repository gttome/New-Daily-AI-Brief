# New Daily AI Brief Command Center — Functional Gap Closure Final Report

## Release identity

- Public working URL: https://npccs.gtome.chatgpt.site
- Repository / branch: `gttome/New-Daily-AI-Brief` / `main`.
- Initial implementation commit: `5b094f02bd65dad28819a58b5d16824ce6bb6fe0`. Follow-up verification changes are recorded in the commit containing this report; the delivered report records the final exact SHA.
- No PR or merge was used; authorized changes were fast-forwarded to main.
- Prior npccs version: **5**, source `3a20629262b8e581c11aeab818f3bce7ae7b18f3`.
- New npccs version: **10**, source `04ef52bdc64cbf2e9475c015441ed0759f7fdffa`.
- New version ID: `appgprj_6ab08a3a6c808191bfeea0371244ee57~appgver_909f7c8b3c588191b7edcbfe43cfd696`.
- Deployment: `appgdep_6ab5fef9ea1081919cd332abc1c04450`, succeeded at `2026-09-25T04:56:32.578315+00:00`.
- Archive SHA-256: `976c3addbaa8475ee905b597faa47894dee219af30e6952bbd1215a3d445131f`.
- Public anonymous access: **PASS**. Native access mode public, revision 2. Anonymous HTML/assets/read APIs and an actual persisted public review were verified without cookies, bearer tokens or owner identity.

## Source reconciliation

Independently verified initial main was `ffae7b31e3cd7f86428ab4811245cabe0eed7a9c`; initial Greenfield Contracts run `36082891607` and Reader Parity run `36082910469` had succeeded. The historical references happened to match the initial current revisions; no reset to historical work was performed.

The deployed v5 source was opened before edits. Its independent-source Refresh adapter, live feed resolution, `Promise.allSettled` behavior, safe fallback and anti-regression checks were carried into `site/command-center/` and extended. GitHub's newer canonical data and UI structure were retained. The repository and Sites use identical functional modules; Sites keeps them under `src/`, while the repository keeps the established `site/command-center/` layout. The compressed immutable data expands during repository builds. No second publishing engine was introduced.

## Functional acceptance

**This is a substantial deployed release, not complete 69-function parity.** The detailed ledger is `docs/COMMAND_CENTER_FUNCTION_LEDGER_2026-09-25.md`; the machine-readable ledger is `evidence/command-center/function-ledger.json`. Exact September 25 assessment names and original statuses are preserved. The packet's additional acceptance requirements remain controlling even where its working row labels differ.

| Coverage | Result |
|---|---:|
| Contract mapping | 10 domains / 30 families; mapping only |
| Functions with deployed implementation | 52 / 69 |
| Functions passing bounded live acceptance | 48 / 69 |
| Functions remaining partial | 13 |
| Intentional exclusions preserved | 4 |
| Original Missing with deployed implementation | 22 / 34 |
| Original Partial with deployed implementation | 18 / 19 |
| Existing Present / Improved preserved or superseded as required | 12 / 12 |

The four intentionally absent functions are not counted as implemented functions. “Live acceptance” is bounded to the evidence cited in each row; it is not an assertion that every possible production operation was performed. Positive real book application was not fabricated, and production publication/repair/Force Replace was not dispatched as a test.

### Exact remaining gaps and access limits

1. **Future canonical operational imports — rows 02 and 23.** Current September 24 inputs were recovered from authenticated GitHub artifact access and are connected. Public GitHub artifact ZIP download cannot supply subsequent canonical inputs to this unauthenticated Worker. Future artifact ingestion needs the existing authenticated publication handoff to include the sanitized projection. No anonymous dispatch or new publisher was introduced to mask this gap.
2. **Seven incomplete historical payloads — rows 39, 42 and 43.** Native source-table export truncated two usage and five snapshot payloads. Those records were excluded rather than fabricated. The two independently truncated evaluation exports were recovered from pinned old Site source, so both evaluation receipts are present. Complete source payloads are still needed for the seven unrecovered records.
3. **Continuing native reader comment collection — row 46.** Twenty-four historical comments and their review surface work. The current ndaib Worker deliberately returns 405 for public comment GET and has no sanitized public comment export. Its existing native table was inspected and had zero rows at migration time. Continuing collection is not connected; a narrowly scoped reader export integration remains necessary.
4. **Authenticated retention cleanup — row 47.** Public verification is non-destructive and produces a receipt. There is no cleanup workflow among the authorized existing canonical GitHub paths and no supported authenticated destructive maintenance surface in this public application. No unrestricted public delete endpoint was added. Actual due cleanup remains unimplemented.
5. **Current native audience/subscription collection — rows 51–56.** All 1,332 accessible historical aggregates were imported and are filterable. The current native reader has no compatible audience event collector/export; its subscription API reports unavailable. Current device/referral/geography, reminder, help/error and attributed-return collection is not connected. These are remaining integration work, not claims that historical reports substitute for current collection.
6. **Positive Applied evidence.** The eight-state write path and evidence rejection are implemented/tested. Real manuscript targets are not mapped into this repository; no real Applied transition was executed. Historical Applied states remain intact with their evidence limitations.
7. **Live browser limitation.** The managed browser supports only the supervised preview. Desktop and 390px browser QA used the matching source; public production HTML/assets/API were verified separately by fresh anonymous HTTP and native unauthenticated-request logs. Production browser rendering is not claimed.

Items 3 and 5 are explicit unfinished integrations, not unavailable data disguised as successful closure. The reader was left unchanged rather than making an unverified cross-Site integration claim.

## Seven correctness fixes

1. **Edition/snapshot mismatch:** projection assembled from actual selected edition records; publication date, item counts and story titles reconcile. Repository head, canonical source and selected publication identity remain distinct. A mismatch does not silently advance the snapshot.
2. **Stale private/publication state:** public runtime and notices replace owner requirements; selected-edition state comes from actual canonical input. D1 last-good state survives failures. Old private-import descriptions remain historical provenance only.
3. **CI / Reader Parity:** rendered as usable run/status/SHA links; failures are visible independently. Component inventory includes workflow history.
4. **Source chart units:** source quantities are counts, not duration/minutes; count-unit regression test passes.
5. **Completion boundary:** `updated_at` is not used as exact completion. Completed job boundaries are required; absent or incomplete job coverage yields unavailable duration.
6. **Contextual evidence:** selected record IDs, dated source paths, canonical run/artifact links and stage evidence replace the generic receipt substitution.
7. **Coverage badge:** separate contract mapping, deployed function coverage, live acceptance, partial count and intentional exclusions. No full-parity badge.

## Data/runtime

- Cloudflare Worker ESM, using the existing Sites project and native D1 `DB` binding. No paid service added.
- D1 tables: `cc_records`, `cc_revisions`, `cc_snapshots`, `cc_migrations`, `cc_rate_buckets`.
- Core mutable records, revision history, migration receipts and snapshots live in D1. Other immutable historical evidence lives in the versioned source/deployment. Browser storage is not authoritative.
- Public read routes under `/api/cc/v1/`: state, health, editions, candidates, media, images, book-proposals, watchlist, sources, qa, incidents, usage, feedback, learning, audience, components, automation and evidence. Existing `/api/refresh` remains connected.
- Typed public writes: proposal revisions, Watchlist reviews and comment reviews; fixed non-destructive imported-comment retention verification.
- Server validates origin, JSON, field allowlist, status, priority and sensitive patterns; maximum request 8,192 bytes, notes 4,096 UTF-8 bytes.
- Limits: 10 accepted write attempts per five minutes / 100 per day per daily-hashed network identity; identifiers and buckets are never exposed publicly. Shared-network fallback is bounded. Local SQL limit tests pass; production rate exhaustion was not induced.
- Idempotency keys bind exact request contents; replay returns the saved event; conflicting reuse is rejected.
- Optimistic base revision plus SQL compare-and-swap protects concurrent writers. Conflict responses retain the browser draft.
- Revision history is append-only; new authorship is `anonymous`; accepted writes are read back.
- Applied requires verified matching repository commit evidence, an allowed changed target path, and the exact proposal ID in the commit message. Anonymous notes alone cannot establish application.
- No anonymous workflow dispatch, production mutation, arbitrary import/SQL or delete route. Existing GitHub permissions remain the production boundary.

## Migrations

| Data | Accessible records retained | Location / verification |
|---|---:|---|
| Core D1 seed | 117 | Actual D1 ID and payload digest read-back: 117 |
| Book proposals | 41 | D1; stable IDs and historical state retained |
| Proposal import receipts | 18 | Immutable versioned source |
| Proposal evaluation receipts | 2 | Independently recovered full source receipts |
| Watchlist topics | 16 | D1; detailed research source timestamps retained |
| Watchlist review/history records | 3 | D1; historical decisions retained |
| Comments | 24 | D1; identifying fields excluded |
| Usage attempts/observations | 32 | D1; raw boundaries and missingness preserved |
| Historical private snapshots | 1 | D1; five unavailable payloads excluded |
| Historical audience aggregates | 1,332 | Complete pagination; immutable versioned source |
| Audience metadata | 2 | Collection bounds retained |
| Ratings / event totals / event days | 133 / 320 / 311 | Immutable versioned source; native aggregates separate |
| All sanitized records | 2,974 | Manifest and deterministic build input |

D1 receipt `seed:cdf80a460eab2312f6fc93e8e274f97979ae23576ea0d2994626d19f312dfa72`: source 117, destination before 0, after 117, inserted 117, duplicates 0, conflicts 0, exclusions 0 for this already-sanitized seed. Read-back checksum `ced24ec89d61bccc12dc9a2ccd093e484f0e5955931720dcec9696ed28711662`, 117 payload digests verified. Completed `2026-09-25T04:17:11.800Z`. Subsequent live health calls return the same receipt with `replay: true`.

The broader preparation receipt excludes 390 sensitive fields and nine truncated source exports, with zero duplicate/conflicting logical inputs. Two of those exports' evaluation records were independently recovered. The seven other inaccessible records were not migrated. Immutable records are not mislabeled as 2,974 D1 rows. Measured zero, null, source timestamps, status history, stable IDs and raw evidence references are preserved.

## Refresh/currentness

- Latest published and selected operational edition: **2026-09-24**.
- Actual canonical workflow run: `36051784007`; source SHA `4a0faf7bc3637bab7d27ee95bfa0dc542e0f958c`.
- Canonical artifact: `10829999743`; ZIP digest `sha256:c40df21b6449177f3e21eac563a5b7b68995d24a558a014d473bed7fe33fa258`.
- Structured edition digest: `sha256:24463a8356510dc5036376ff05b3c113d79701cc6b8c03f20edf277c8dcc4a2e`.
- Recorded projection base SHA `ffae7b31e3cd7f86428ab4811245cabe0eed7a9c` remains explicitly separate from live repository head.
- Latest attempted run is returned separately from latest publication. Current publication count and story-title reconciliation passed.
- Actual canonical saved run is `build_locked`; the release does not invent later canonical stage completion from a successful Site publication.
- Verified last-good snapshot saved to D1 and read back, including reload/failure tests. Native reader signal snapshots deduplicate unchanged aggregate content.
- Partial failure: local integration independently removed all upstream sources and retained verified state without a new success timestamp; preview visibly reported unavailable sources.

## Tests

- **20 focused JavaScript tests PASS**, real SQLite adapter implementing the D1 interface; actual migrated records used for integration tests. Includes all eight states, Applied guard, origin/payload validation, idempotency, concurrent conflict, rate limit, deterministic migration replay, identity, missing-vs-zero, denominators, durations, contextual evidence, source units and prohibited production endpoints.
- **17 focused Python tests PASS** for state/schema migration, parity validation and existing Command Center contracts. Full v2 schema validation also passed locally.
- Bounded repository validation PASS; initial router expectation failure was corrected and its initial evidence retained separately. No full-system validation was requested or dispatched.
- Initial post-implementation Greenfield Contracts CI `36093938004` succeeded on `5b094f02bd65dad28819a58b5d16824ce6bb6fe0`. Final follow-up CI result is recorded in the delivered report.
- Reader Parity `36082910469` success reused for unchanged reader inputs. No production publication, repair or Force Replace was dispatched to test controls.
- Anonymous live acceptance: **25 checks PASS**, all fifteen main read areas, actual D1 proposal write/read-back, replay, stale-revision conflict, and denied dispatch/Force Replace/publish endpoints. Final version follow-up: **15 additional checks PASS**, including actual Watchlist and comment writes/read-back, ten-item native ratings, 16-topic interest, 17-component inventory, live workflow history and rejected Applied/origin/oversized writes. Evidence is in `final-live-acceptance.json`.
- Public exposure scan covered complete imported data, projection, API serialization, downloadable guide and bundled assets: no recognized secret/email/authentication value matches; 390 excluded fields. Pattern/field scans cannot prove that arbitrary free text contains no identifying meaning; that limitation is explicit.

## UI QA

Existing section hierarchy, pipeline and visual structure retained; a bounded evidence/review explorer and onboarding were added. Every evidence area was opened in the managed browser.

- Desktop: body width / scroll width **1348 / 1348**; no page overflow.
- Approximately 390px: iframe width 390, content width / scroll width **375 / 375**; no page overflow. Wide tables have contained scrolling.
- Keyboard tab switching, visible focus, dialog Escape, empty filters, unavailable/stale Refresh and concurrent revision conflict were checked.
- Proposal, Watchlist and comment forms saved and read back in the preview. A desktop/mobile conflict kept the second draft after a 409 response.
- Imported-comment retention verification displayed its bounded scope and receipt read-back.
- Live HTTP verified UI and assets anonymously; native logs marked those requests unauthenticated. Production desktop/mobile browser rendering was not available in this environment.

## Manual controls

| Control | Verification |
|---|---|
| Build Entire Brief | Existing `manual-daily-brief.yml` launch link; no dispatch |
| Resume Current Edition | Same canonical workflow, selected edition instructions, force replacement off |
| Force Replace | Existing canonical workflow; history through 2026-09-23 remains guarded |
| Rerun Failed Bounded Stage | Exact failed run when available; disabled when unsupported/unavailable |
| Validate Reader | Existing `reader-parity.yml` link; no test dispatch |
| Refresh State | Actual source reconciliation plus D1 last-good read-back |
| Open Current Run | Exact returned canonical run URL |
| Open Publication Artifact | Exact selected canonical run artifact |
| Open Live Brief | Selected edition route on ndaib |
| Open Repository State | Current repository main |
| View Exact Evidence | Selected edition/record/stage evidence IDs and provenance |

Opening GitHub launch pages does not pre-authorize production actions or guarantee GitHub form fields are filled. Existing workflow permissions and explicit input selection remain required.

## Safety / boundaries

- Old `gttome/Daily-AI-Brief` production and old Command Center changed: **NO**. Old Site remains version 56.
- `ndaib` behavior changed: **NO**. Reader remains version 4; read-only integration calls only.
- Paid service added: **NO**.
- Automatic editorial weighting enabled: **NO**.
- Email/text delivery enabled: **NO**.
- Publisher 07:00 America/Chicago created/enabled: **NO / NO**.
- Validation/Repair 09:00 America/Chicago created/enabled: **NO / NO**.
- Old schedules modified: **NO**.
- Cutover/decommission performed: **NO**.
- No second RunEngine, publisher, reader pipeline or Command Center publishing engine.

## Rollback

- Original repository rollback anchor: `ffae7b31e3cd7f86428ab4811245cabe0eed7a9c`.
- Original npccs v5 source: `3a20629262b8e581c11aeab818f3bce7ae7b18f3`; prior v8 public runtime source: `e7df83dd36d30e73ec091866dcabfc4293dc50c9` is the closer rollback for v9-only fixes.
- Re-deploy a previously saved native version; preserve D1 tables and append-only revision history. Do not drop storage to roll back UI code.
- An emergency rollback to v5 must restore private access because that implementation predates the public safety model. Rolling back code does not undo public disclosure already made.
- Correct reviews by a new explicit revision. Preserve migration receipts and source input digests; never overwrite historical decisions to conceal a correction.


## Final provenance correction

Version 10 derives the canonical run ID from the actual selected artifact URL when source records omit an explicit run field. The real-import regression test asserts run `36051784007`; all 20 tests pass. Public GitHub metadata may be rate-limited independently; the API reports each source failure rather than asserting a current SHA or CI result. The separately authenticated GitHub CI check remains valid evidence. Version 9 remains a rollback point at source `8071779c62404fbfc6ab094a407724c17aa600f4`.
