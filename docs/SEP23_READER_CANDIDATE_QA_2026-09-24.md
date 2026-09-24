# September 23 reader candidate QA

Candidate continues the published Site source 9cd74e329329a76592e8a3ee23eab88c68836f05
with the canonical reader corrections in PR 103. No editorial selection or
accepted image work was repeated. The legacy system remains untouched.

- GitHub Greenfield Contracts 35952758597: passed.
- GitHub Reader Parity Validation 35952758596: passed; 38 editions reconciled.
- Static candidate: 342 HTML pages, 38 editions, all required pages and feeds.
- All internal href/src references across those pages resolve locally.
- Six permanent story pages: correct images, verified source reading estimates,
  summaries, Why It Matters, sources, related coverage and feedback controls.
- Two video and two podcast permanent pages: present with reading/runtime
  information, source links, ratings, comments and sharing controls.
- Desktop browser at 1363px: all ten item pages fit, no broken images.
- Small-screen browser QA: actual 390px iframe viewport in the supervised
  preview, covering home, dated brief, six stories, four media pages, Watchlist,
  archive, Sources, About and Subscribe. This tests responsive layout, not a
  physical phone or touch-device emulation. Six images load at 339px within the
  available 375px document width. Screenshot inspection found an archive input
  overflow, now fixed in the canonical builder and visually rechecked.
- Isolated preview ratings confirmed on a story and the second podcast.
- Isolated preview private comment confirmed on the second podcast.
- Watchlist interest confirmed; 16 topics load with preserved research history.
- Share dialog targets the permanent item URL and offers the established
  channels. No external share or email message was sent during QA.
- SQLite-backed API tests: retry idempotency, invalid origin/item/value rejection,
  event counts, private comments, retention cleanup, Watchlist revision safety,
  and disabled email signup all pass. Local QA data is never copied to production.

Six accepted 1200x630 WebP image bindings remain in place: three existing
accepted images and three reviewed native OpenAI replacements, with original
image bytes retained. Watchlist: 0 new, 3 updated, 13 carried forward.

Candidate Critical/High defects remaining: zero after archive overflow repair.
The final patch still needs GitHub checks, merge and native publication. Live
production verification must be recorded separately after deployment.

The GitHub artifact download reference returned HTTP 403 in this environment.
Publication therefore resumes the already checked-out native Site reader
source and applies the same canonical correction/runtime functions, rather
than reconstructing or regenerating historical editorial content. Source
provenance must retain both the prior Site source and final main commit.
