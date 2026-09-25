# Command Center Data Parity Standard

**Document type:** Living architecture and data-governance standard  
**Repository:** `gttome/New-Daily-AI-Brief`  
**Status:** Active living document  
**Effective date:** 2026-09-24  
**Owner:** New Daily AI Brief  
**Applies to:** New Daily AI Brief, New Daily AI Brief Command Center, migration/cutover work, private owner-data services, and any future Command Center data adapter

---

## 1. Purpose

This document defines the permanent data-parity requirement between the current Daily Generative AI Brief Command Center and the New Daily AI Brief Command Center.

The objective is not visual similarity. The objective is **operational-data equivalence or improvement**.

For every legitimate data element available to the current Command Center, the new system must do one of the following:

1. provide equivalent data at equal fidelity;
2. provide improved data with stronger provenance, history, or precision; or
3. explicitly document that the data has been deliberately retired, including the reason and owner approval.

A current data element must never disappear silently during migration, refactoring, or cutover.

This file is the authoritative living record of that requirement and must be updated whenever Command Center data is added, removed, renamed, materially redefined, moved between public/private boundaries, or changes source-of-truth.

---

## 2. Governing principles

### 2.1 Data-contract parity, not UI imitation

Parity is measured at the data-contract and operational-record level. A dashboard card may change presentation, but the underlying legitimate information must remain traceable and available.

### 2.2 Canonical evidence first

The new Command Center must read from canonical greenfield artifacts and approved private owner-data stores. It must not infer operational truth from rendered reader pages when a durable machine-readable record exists.

### 2.3 No silent data loss

Every current data family must have a documented destination state:

- `equivalent`
- `improved`
- `deliberately_retired`
- `not_yet_implemented`

`not_yet_implemented` is acceptable during development but blocks final parity/cutover for any required data family.

### 2.4 Unknown is not zero

The system must preserve the distinction among:

- measured zero;
- unknown;
- unavailable;
- suppressed;
- stale;
- not applicable;
- not recorded.

No adapter may replace missing evidence with zero or a healthy state.

### 2.5 Public and private data remain separate

Operational data safe for repository/public transport and private owner-only data must use separate approved paths. Private owner data must not be copied into the public repository merely to simplify synchronization.

### 2.6 Historical continuity matters

Parity includes history, not only today's edition. Where authoritative legacy records exist, the new Command Center must preserve or reference the historical record at the appropriate fidelity.

### 2.7 Every displayed value must be traceable

Every operational value shown in the Command Center must be traceable to one or more:

- canonical greenfield artifacts;
- versioned repository records;
- GitHub workflow/run metadata;
- approved private data records;
- native Site/runtime records where they are the authority.

---

## 3. Source-of-truth hierarchy

When sources disagree, use this order unless a later approved architecture document explicitly supersedes it:

1. Current explicit owner instruction.
2. Current canonical New Daily AI Brief artifacts produced by the greenfield `RunEngine`.
3. Approved private owner-data stores for private-only domains.
4. Versioned New Daily AI Brief operational records and receipts.
5. Migrated legacy operational records for historical periods not yet represented natively.
6. Legacy Daily AI Brief repository records for pre-cutover history.
7. Rendered pages only when no machine-readable authoritative record exists.

The new Command Center must never treat its own cached display snapshot as the underlying source of truth.

---

## 4. Current architecture baseline

### 4.1 Current Daily AI Brief data plane

The current system has a broad effective operational data plane composed of:

- canonical edition data;
- story-memory and novelty data;
- candidate/editorial records;
- discovery and evidence records;
- image-generation and image-quality records;
- media records and media preflight;
- Watchlist records, discovery, sweeps, and source state;
- QA and QA history;
- accessibility records;
- analytics records;
- trends;
- incidents, publication records, releases, operations, and append-only ledgers;
- efficiency and attempt telemetry;
- editorial feedback and editorial learning;
- personal feedback;
- source reliability;
- private Usage History;
- private Book Change Proposals and owner decisions.

The current repository contains these top-level operational record families under `_records/`:

- `accessibility`
- `analytics`
- `attempts`
- `command-center`
- `discovery-preflight`
- `discovery`
- `editorial-feedback`
- `editorial-handoff`
- `editorial-learning`
- `editorial`
- `efficiency`
- `image-quality`
- `images`
- `ledgers`
- `operations`
- `personal-feedback`
- `publication`
- `qa-history`
- `qa`
- `releases`
- `source-reliability`
- `trends`
- `watchlist-discovery`
- `watchlist-sweeps`
- `watchlist`

The legacy `_data/` layer also includes canonical editions, Story Memory, source registries, Watchlist state/discoveries/sources, media candidate data, book-reading mappings, reading-support data, early-signal sources, and operating policies.

### 4.2 Current New Daily AI Brief Command Center data path

The current new Command Center snapshot builder, `scripts/build_command_center_snapshot.py`, primarily reads:

- the latest publication receipt;
- migrated legacy edition data;
- migrated legacy Watchlist data;
- migrated legacy source registry;
- migrated legacy Watchlist source state;
- migrated legacy book-reading mappings;
- new media-source configuration;
- the existing Command Center state template.

The resulting `site/command-center/state.json` is useful as a sanitized fallback snapshot, but it is **not yet a full replacement for the current Command Center data plane**.

### 4.3 Existing greenfield canonical projection

The greenfield system already contains a canonical Command Center projection model based on the following artifact chain:

`discovery → edition → rating-contract → media → watchlist → book-bridges → images → publication-bundle → reader-render → route-manifest → release-package → shadow-deployment → live-verification → book-change-evaluation`

That projection already binds artifacts by digest and carries important normalized operational data. It is currently shadow-only and production/private-live projection is intentionally fail-closed until an approved production adapter exists.

The production implementation must extend this existing canonical projection. It must not create a second competing Command Center pipeline.

---

## 5. Required data domains

The parity contract is organized into ten required domains.

### A. Editorial and discovery

The new Command Center must receive, where authoritative records exist:

- source scans;
- candidate count;
- candidate IDs;
- candidate titles and canonical URLs;
- candidate category/focus;
- candidate scoring;
- scoring dimensions;
- ranking;
- selected/rejected state;
- rejection reason;
- editorial rationale;
- source reliability/authority classification;
- evidence classification;
- evidence claims/packets;
- discovery metadata;
- evidence retrieval/deep-review counts;
- novelty result;
- prior-story matches;
- material-update reasoning;
- exactly-one Agent Skills designation;
- final 2/2/2 allocation.

### B. Edition, story, image, and media content

The new Command Center must receive:

- edition ID/date/status;
- all six selected story IDs;
- headline;
- summary;
- Why It Matters;
- What To Do Now;
- source organization;
- source URL;
- source publication date;
- reading-time evidence;
- topic/company metadata when present;
- permanent story URL;
- image ID/path/digest;
- image dimensions/format;
- image generation method when recorded;
- image attempts/rejections/acceptance;
- image QA result and rejection reason;
- two selected videos and verification metadata;
- two selected podcasts and verification metadata;
- media source and freshness evidence;
- public reader book bridges.

### C. Emerging AI Watchlist

The new Command Center must receive:

- full active topic list;
- topic IDs/names;
- new today;
- updated today;
- carried forward;
- removed;
- source evidence;
- discovery/sweep evidence;
- semantic-refresh state where applicable;
- Watchlist source registry;
- source retrieval/availability state;
- source-state timestamps;
- historical Watchlist changes.

### D. Quality, QA, and accessibility

The new Command Center must receive:

- initial QA state;
- final QA state;
- individual QA checks;
- severity;
- failure class;
- repair action;
- repair result;
- recurring defect categories;
- image QA;
- link/source health;
- route integrity;
- feed/archive integrity;
- desktop verification;
- mobile/small-screen verification;
- deterministic accessibility results;
- editorial/manual accessibility review where available;
- historical QA and accessibility records.

### E. Publication and infrastructure

The new Command Center must receive:

- publication transaction identity;
- repository SHA;
- publication/release receipts;
- CI/check status;
- build status and duration where authoritative;
- changed route/file evidence where available;
- deployment/Site state;
- Site version where safe;
- reader bundle identity;
- route manifest;
- archive/feed generation state;
- live smoke/live verification;
- current live edition URL;
- currentness watermark.

### F. Run and production telemetry

The new Command Center must receive:

- run ID;
- attempt ID;
- run mode;
- completion state;
- lifecycle state;
- start/end time;
- elapsed time;
- per-stage timing where recorded;
- attempt count;
- retry count;
- resume count;
- recovery target;
- source scans;
- deep retrievals;
- media checks;
- image drafts;
- image rejects;
- accepted-image count;
- QA counts;
- repair counts;
- anti-rework statistics;
- artifact reuse/rebuild counts;
- completion receipt state.

### G. Reader signals and analytics

Where authoritative and privacy-safe, the new Command Center must receive:

- rating totals;
- rating distribution;
- shares;
- comments;
- read-event activity;
- source clicks;
- video engagement;
- Watchlist engagement;
- retention/directional analytics where legitimately recorded;
- small-count suppression status;
- date range;
- data maturity/limitations;
- analytics availability state.

### H. Intelligence and editorial learning

The new Command Center must receive:

- Trend Radar state;
- trend classification;
- trend window;
- supporting stories/signals;
- editorial feedback;
- personal editorial feedback where appropriate;
- editorial-learning sufficiency;
- complete rated editions;
- rating counts by focus;
- candidate-set comparison counts;
- proposed practical-value adjustment;
- protected scoring dimensions;
- approval state;
- active/inactive state;
- active-edition limit;
- expiry;
- rollback triggers.

### I. Governance, incidents, corrections, components, and automation

The new Command Center must receive:

- incident ID;
- severity;
- detection;
- evidence;
- assessment;
- corrective action;
- validation;
- approval;
- rollback;
- resolution;
- recurrence linkage;
- alert state/fingerprint where applicable;
- correction history;
- original/corrected fact;
- affected pages;
- correction reason;
- owner approval queue;
- component health;
- component version;
- last activity;
- last success;
- known issues;
- configuration version history;
- workflow/automation safe name;
- schedule;
- enabled state;
- last run;
- last success;
- failure history;
- change/version summary;
- production-readiness gates and evidence.

### J. Private owner-only data

The private new Command Center must support a separate authenticated data path for at least:

- Usage & Recorded Production Effort;
- authoritative edition-attributed Work/Codex/credit measurements when available;
- Book Change Proposals;
- Pending review / Approved / Rejected;
- proposal source edition/item;
- target book;
- proposed change;
- evidence/reason;
- suggested teaching asset where applicable;
- stable dedupe identity;
- owner decision persistence;
- private comments or owner-only annotations where approved.

These records must not be moved into the public GitHub repository merely to simplify the implementation.

---

## 6. Current parity implementation register

The 2026-09-24 data-parity implementation maps every required family in
`config/command-center-data-parity.json`. The repository carries public-safe
canonical data and immutable historical references; authenticated owner-only
values remain outside the public repository.

| Area | Implemented state |
|---|---|
| Candidate funnel and scoring | Improved — canonical discovery is projected and legacy candidate/discovery history is referenced at the pinned legacy SHA. |
| Evidence packets and detailed novelty/Story Memory | Improved — canonical discovery payload is projected; authoritative legacy Story Memory/evidence history is preserved by reference. |
| Discovery/retrieval telemetry | Improved — native run/validation evidence is used where available and legacy discovery/efficiency records remain referenced without invented values. |
| Full attempt/run history | Improved — canonical run/completion evidence is combined with immutable legacy attempt references; private usage merges only through the authenticated adapter. |
| Exact stage timings | Equivalent where recorded — exact native/legacy timing is surfaced when authoritative; missing timing remains unavailable. |
| Image generation/rejection history | Improved — canonical image payload is projected and legacy image/image-quality history is referenced. |
| Full QA/repair history | Improved — native bounded-validation evidence plus immutable legacy QA/QA-history references. |
| Accessibility history | Equivalent — authoritative legacy accessibility history is retained by reference and native checks append going forward. |
| Efficiency/production-effort history | Improved — legacy efficiency boundaries are preserved and never silently merged. |
| Usage/credit evidence path | Improved — `PrivateOwnerDataStore` supplies an authenticated-private persistence contract; credits remain unavailable without authoritative evidence. |
| Ratings/distribution | Equivalent/improved — native authoritative aggregates may be used; legacy analytics remain referenced; unknown values are never fabricated. |
| Shares/clicks/read events/video engagement | Equivalent — authoritative runtime values only, with legacy analytics references and suppression/missingness preserved. |
| Editorial feedback/learning | Equivalent — legacy learning/feedback history is referenced and native records can supersede it. |
| Trend Radar | Equivalent — complete legacy trend history remains available by immutable reference. |
| Correction ledger | Equivalent — append-only legacy correction ledger is preserved by reference. |
| Detailed incident/alert history | Improved — canonical incident/recovery evidence plus legacy Command Center/operations history. |
| Component/configuration history | Improved — repository/workflow evidence plus legacy release/source-reliability references. |
| Automation history | Improved — GitHub workflow metadata plus legacy attempt/release history; new schedules remain cutover-blocked. |
| Private Book Change Proposals | Improved — authenticated-private CRUD/dedupe/status/reload contract implemented; proposal values are never committed publicly. |
| Multi-edition operational history | Improved — `config/command-center-legacy-history.json` pins the authoritative historical families to the legacy SHA. |
| Production greenfield Command Center projection | Improved — the existing canonical projection now includes complete operational-domain payloads and provenance; live/private materialization remains intentionally cutover-gated rather than bypassing the production-safety gate. |

No required family is marked `not_yet_implemented` in the machine-readable
matrix. A future cutover still requires the separately requested Full System
Validation and the other cutover gates in this standard.

---

## 7. Required implementation architecture

### 7.1 Production Command Center projection

Extend the existing greenfield `command-center-projection` so it becomes the single normalized operational projection for the new Command Center.

The projection must:

1. read the canonical greenfield artifacts;
2. validate schema/version;
3. bind each value to canonical content digests;
4. preserve zero/missing/unavailable semantics;
5. carry historical references when applicable;
6. exclude private owner-only values from public-safe output;
7. produce an identity-bound freshness watermark;
8. fail visibly on unsupported or mismatched data.

### 7.2 Private data plane

Private owner-only data must use a separate approved authenticated store/service.

Minimum private capabilities:

- create/read/update Book Change Proposals;
- persistent Pending/Approved/Rejected decisions;
- idempotent import/evaluation;
- Usage History by edition and attempt;
- dedupe by stable IDs;
- metric-level missingness;
- private comment/annotation persistence where approved;
- no false success on failed writes.

### 7.3 Historical reconciliation

Historical parity must use authoritative legacy records without rewriting history.

The reconciliation must:

- preserve legacy record IDs and dates where meaningful;
- never invent missing measurements;
- preserve incompatible measurement boundaries rather than merging them silently;
- reference legacy records when a full migration is unnecessary;
- keep private records private;
- produce a durable mapping between legacy records and new Command Center representations.

### 7.4 Freshness/currentness

The normal state path must be:

`canonical Brief run → Command Center projection → private Command Center synchronization → projection watermark → UI`

The Command Center must classify projection state using identity/digest semantics:

- Current
- Stale
- Missing
- Mismatched
- Unsupported

The browser clock must never be used as proof that data was successfully refreshed.

---

## 8. Machine-readable parity matrix

A companion machine-readable matrix should be created during implementation and maintained in the repository's configuration area under the filename **command-center-data-parity.json**.

Each record must include at least:

- `domain`
- `data_family`
- `current_source`
- `current_private_or_public`
- `new_authoritative_source`
- `new_command_center_destination`
- `historical_requirement`
- `status`
- `validation_method`
- `notes`
- `last_reviewed_at`

Allowed `status` values:

- `equivalent`
- `improved`
- `deliberately_retired`
- `not_yet_implemented`

Any `deliberately_retired` record must include explicit owner approval and rationale.

---

## 9. Command Center Data Parity Validation

A dedicated validation activity must compare the current and new systems by data family.

For every required row, validation must answer:

- Does the new Command Center receive the data?
- Is historical depth equivalent where authoritative history exists?
- Is the value semantically equivalent?
- Is its source authoritative?
- Is freshness/currentness equivalent or stronger?
- Are zero/missing/unavailable semantics preserved?
- Is privacy equal or stronger?
- Can the displayed value be traced to canonical evidence?

Final cutover requires:

- zero unexplained missing required data families;
- zero private-data leakage defects;
- zero unsupported schema silently accepted;
- zero currentness mismatches;
- zero unresolved Critical/High defects.

This parity validation is distinct from the repository-wide Full System Validation defined in `docs/TESTING_AND_VALIDATION_STANDARD.md`.

---

## 10. Implementation phases

### Phase 1 — Freeze data inventory

- complete the machine-readable current-to-new parity matrix;
- identify public/private ownership for every data family;
- identify historical backfill/reference requirements;
- mark every row with one allowed parity status.

### Phase 2 — Extend canonical greenfield projection

- extend the existing greenfield Command Center projection;
- use real canonical RunEngine artifacts;
- add missing editorial, evidence, QA, operations, analytics, history, and governance domains;
- preserve artifact digest bindings and currentness watermarking.

### Phase 3 — Implement private owner-data plane

- Usage History;
- Book Change Proposals;
- owner decisions;
- private records;
- dedupe;
- persistence;
- privacy tests.

### Phase 4 — Reconcile history

- map/import authoritative legacy operational history;
- preserve missingness;
- preserve incompatible measurement boundaries;
- reconcile multi-edition history.

### Phase 5 — Connect the private Command Center

- make the private Command Center consume the complete production projection and private owner-data plane;
- keep `state.json` only as a safe fallback snapshot;
- do not use migrated legacy snapshots as the permanent live data source.

### Phase 6 — Data-parity validation

- run the dedicated Command Center Data Parity Validation;
- resolve all unexplained gaps;
- record durable evidence.

### Phase 7 — Full System Validation and cutover

- run Full System Validation only as a separately requested activity;
- cut over only after parity, privacy, and full-system gates pass.

---

## 11. Cutover acceptance criteria

The new Command Center may replace the current one only when:

1. every required current data family has a documented mapping;
2. no required current data silently disappears;
3. every new displayed value traces to authoritative evidence;
4. historical depth is preserved where records exist;
5. private/public separation is equal or stronger;
6. Usage History is operational;
7. Book Change Proposals are operational and persistent;
8. candidate/editorial/evidence/novelty detail is available;
9. QA/repair/accessibility history is available;
10. analytics/reader signals are available where authoritative;
11. trends/editorial-learning data is available;
12. incident/correction/approval history is available;
13. attempt/runtime/efficiency history is available;
14. automation/component/configuration history is available;
15. projection freshness is identity-bound and provable;
16. Command Center Data Parity Validation reports zero unexplained gaps;
17. required development/integration tests pass;
18. separately requested Full System Validation passes;
19. no unresolved Critical or High defects remain.

---

## 12. Living-document maintenance policy

This document must be updated in the same change set whenever any of the following occurs:

- a Command Center data field/family is added;
- a data field/family is removed;
- a field changes meaning;
- a source-of-truth changes;
- public/private classification changes;
- retention/history behavior changes;
- a schema changes materially;
- a new analytics/engagement signal is introduced;
- a new incident, correction, approval, learning, Watchlist, or telemetry family is introduced;
- a data family is intentionally retired;
- a new historical migration rule is introduced.

A PR that materially changes Command Center data without updating this document and the machine-readable parity matrix is incomplete.

---

## 13. Change log

| Date | Change |
|---|---|
| 2026-09-24 | Initial living standard created from current-vs-new Command Center data audit and parity plan. |
| 2026-09-24 | Implemented the machine-readable parity matrix, immutable legacy-history index, enriched canonical projection domains, authenticated-private owner-data store contract, public-safe state bindings, and dedicated Command Center Data Parity Validation. |
