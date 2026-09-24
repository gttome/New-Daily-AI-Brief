# New Daily AI Brief — Final ChatGPT Site Publication Handoff

**Prepared:** September 23, 2026  
**Target reader Site:** https://ndaib.gtome.chatgpt.site  
**Greenfield repository:** `gttome/New-Daily-AI-Brief`  
**Verified source SHA:** `e3a765c259e7e2ef8d59570e9353c09a57031804`  
**Status:** Reader implementation complete and verified; final ChatGPT Site publication is blocked only by unavailable native Sites publish/project tooling in the current chat.

## Do not redo completed work

Do not repeat the migration, reader rebuild, historical import, reader parity build, canonical RunEngine verification, PRs #95/#96, CI, engineering-preview deployment, or live smoke tests.

The exact verified reader bundle already exists as GitHub Actions artifact:

- Workflow: Reader Parity Validation run `35941992171`
- Artifact ID: `10784968502`
- Artifact name: `ndaib-reader-parity-e3a765c259e7e2ef8d59570e9353c09a57031804`
- Artifact digest: `sha256:75813307a9116270db32b4f01512f952e96e55f5414f288864a4b790fdb869b7`
- Artifact size: 70,669,179 bytes

## Completed and verified

- Legacy production snapshot pinned at exact SHA `4ac06268048a3241d2ecaa5ce7c2638266500d75`.
- Historical migration cutoff enforced at September 23, 2026.
- Machine-readable parity manifest persisted at `evidence/reader-parity/data-parity-manifest.json`.
- 38 dated editions retained through September 23.
- 239 story pages retained.
- 209 reader images retained.
- 20 permanent video pages retained.
- 21 permanent podcast pages retained.
- 221 archive entries retained.
- 221 feed entries retained.
- 33 book-bridge records retained.
- 342 rendered HTML reader routes validated.
- Six September 23 story images validated.
- Ratings, share/events, and comments transports retained in place without inventing historical values.
- Reader contains no Command Center link and no greenfield test labels.
- Canonical manual operation path calls `start_daily_brief(...)` / `RunEngine`; no duplicate publisher was created.
- Bounded change classifier prevents reader-only changes from rerunning the historical 50–80 minute full regression suite.
- Greenfield Contracts passed on final SHA.
- Reader Parity Validation passed on final SHA.
- Reader Parity Engineering Preview build/deploy/live-smoke passed on final SHA, including desktop and phone user-agent checks.

## Verified engineering preview

The verified engineering preview is:

https://gttome.github.io/New-Daily-AI-Brief/

This preview is engineering evidence only. It is not the final reader URL and must not be presented as the production replacement.

## Remaining action — exactly one boundary

Publish/synchronize the already verified reader bundle to the existing ChatGPT Site:

https://ndaib.gtome.chatgpt.site

The current chat has GitHub, Files, web, and plugin-management capabilities but does **not** expose native ChatGPT Sites project/publish tools. Plugin discovery also found no ChatGPT Sites publishing connector. Therefore the current chat cannot truthfully claim the target Site has been updated.

A Sites-enabled continuation must:

1. Open the existing Site identified by slug `ndaib`; do not create a replacement Site.
2. Use source SHA `e3a765c259e7e2ef8d59570e9353c09a57031804` and the existing verified bundle/artifact above as the sole publication source.
3. Do not rebuild, redesign, regenerate, or re-import reader history.
4. Publish/synchronize the reader to `https://ndaib.gtome.chatgpt.site`.
5. Verify desktop and small-screen parity on the actual ChatGPT Site for homepage, archive, one old edition, September 23 edition, Watchlist, Sources, About, Subscribe, rating/share/comment controls, and permanent article/video/podcast routes.
6. Verify no Command Center link, no internal GitHub/CI/evidence link, and no test-only label is reader-visible.
7. Record actual Site publication/project revision and live verification evidence.
8. Only after those checks may the reader program be marked fully complete.

## Retry rule

On every retry, resume from this checkpoint and the repository's current durable records. Do not redo completed migration, implementation, CI, reader bundle generation, or live engineering-preview verification unless a new repository change invalidates them.
