# September 23 reader repair checkpoint

Status: NOT COMPLETE; existing ndaib Site version 2 remains live. No new publication authorized while known High defects remain.

Base main: 12a1154f3de1ad1c9cf56b3bdf8d1f4b2bbea1c0. Greenfield Contracts and Reader Parity Validation passed on this base. Canonical workflow treats September 23 as the protected authoritative historical package. Discovery/editorial/media selection was not repeated. No duplicate publishing pipeline.

## Reader corrections in this branch
- Root-site Watchlist fallback no longer replaces the valid empty base URL with /Daily-AI-Brief.
- Six permanent stories inherit their already verified reading estimates from the immutable September 23 edition.
- Three native OpenAI image corrections: Nemotron wrong-story binding, OpenTelemetry overlapping heading, JetBrains clipped footer. All 1200×630 WebP, visually reviewed. Original bytes retained. Manifest binds exact canonical story IDs and source/corrected hashes.
- Existing reader builder applies these corrections; bounded regression checks reject changed historical image bytes. Static validation does not certify live transport or mobile behavior.

## Verified current live state
Homepage, dated edition and all six permanent stories, two video pages and two podcast pages load. All six current images load at 1200×630, but the image corrections above are not live. Sources, About, Subscribe and Archive load. Daily RSS is HTTP 200 and contains 38 editions, newest September 23. Local published payload has 342 HTML routes and 38 dated editions. Share and comment dialogs open; no real comment/rating was submitted.

Watchlist homepage counts are 0 new, 3 updated, 13 carried forward. The full Watchlist currently fails to load because of the incorrect base path. Desktop layout inspected. True small-screen visual QA remains outstanding; previous phone user-agent HTTP checks are not mobile visual evidence.

## Shared-service boundary requiring user permission
The existing legacy-shared feedback service rejects ndaib's Origin. OPTIONS for /api/ratings, /api/events and /api/comments returned 204 with Access-Control-Allow-Origin: null. Source inspection additionally found a separate Watchlist write-origin restriction and a legacy singular-podcast-only item validator.

The separate proposed patch at docs/proposed-shared-feedback-sep23.patch is NOT APPLIED. It adds the exact ndaib origin alongside the existing GitHub Pages origin, uses the same allowlist in comments and Watchlist voting, and recognizes included items from the podcasts array. No wildcard, database migration, historical counter change, authentication removal or privacy/retention change. It is scoped to the September 23 migrated item identities; later greenfield-only editions will require their canonical item registry integration.

User instruction 19 prohibits modifying the legacy production system or separate Command Center. Therefore no shared-service source was changed or deployed. Approval is needed for this narrow shared-service exception before complete feedback verification and publication can finish.

## Remaining gates
1. Pass GitHub candidate CI and retain its artifact.
2. Obtain explicit permission for and verify the prepared shared-feedback repair.
3. Verify full reader, actual small-screen layout, image binding and live interactions.
4. Publish only the existing ndaib Site after all High/Critical defects are closed; retain history and original images.
5. Verify live Site and reconcile durable completion. Do not mark Complete based on the existing publication alone.
