# Iteration 32 Owner Acceptance Checklist
## Interim stop gate — test access only

Use only after the Iteration 32 deployment workflow reports success.

### Reader
- Open the greenfield reader URL on desktop.
- Open the same reader URL on a phone/small screen.
- Confirm the **GREENFIELD TEST · PRE-CUTOVER** label is obvious.
- Open Current edition, Archive, Watchlist, Media, and at least one Article.
- Set a 1–5 star rating, change it, refresh, and confirm local persistence.
- Test Share on an article and a media item.
- Confirm six representative stories appear in the locked 2 / 2 / 2 allocation.

### Command Center
- Open the Command Center URL directly; no owner-only key or URL fragment is required.
- Confirm it shows run identity/status, QA/readiness, freshness/currentness, recovery/resume, and production separation.
- Confirm the displayed deployed source SHA is present.
- Open it on a phone/small screen and confirm cards reflow to a single column.
- Confirm the page contains representative test state only and exposes no credentials, secrets, private IDs, prompts, or production-control capability.

### Coexistence / safety
- Confirm the greenfield reader is clearly separate from the production Daily AI Brief.
- Confirm no production cutover or reader rerouting is implied.
- Do not treat representative test content as a production publication.

### Stop rule
After these checks, report defects or acceptance results. Iteration 32 must remain open and Iteration 33 must not begin until the owner explicitly resumes work.
