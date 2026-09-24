# September 23 continuation: NDAIB-owned feedback

The user clarified that New-Daily-AI-Brief and the existing ndaib Site may be
changed. The legacy Daily-AI-Brief system and shared feedback service remain
untouched. The earlier proposed shared-service patch is superseded and must
not be applied.

PR 103 continues the existing completed September 23 editorial package. It
does not repeat discovery, media selection, or accepted image generation.
Three accepted image repairs retain the original assets and exact canonical
story bindings. The six story reading estimates, Watchlist root path, and
related coverage are repaired by the canonical reader builder.

The same builder attaches an NDAIB-owned feedback Worker and generated D1
schema to its candidate artifact. All product feedback calls use same-origin
API endpoints. Published item IDs are derived from the candidate reader, so
both podcasts and all migrated item pages are covered. Six bounded runtime
tests pass locally, including retry safety, origin validation, private
comments, retention cleanup, watchlist revisions, and disabled email signup.

Still required before publication: current PR CI, complete candidate reader
QA at desktop and narrow viewport, merge to current main, native Site save
and deployment, then live verification. Production remains version 2 until
those gates pass. This checkpoint is not a publication-complete assertion.
