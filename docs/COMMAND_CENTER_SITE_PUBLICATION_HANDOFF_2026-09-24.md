# New Daily AI Brief — private Command Center Site publication handoff

**Target Site identifier:** `npccs`  
**Required access:** private / owner-only  
**Source:** `gttome/New-Daily-AI-Brief` current `main`, directory `site/command-center/`

## Publication source

Publish exactly the Command Center source committed under `site/command-center/`: `index.html`, `cc.css`, `cc.js`, and `state.json`. Do not attach the public reader shell, do not publish this directory to public GitHub Pages, and do not recreate a second publishing pipeline.

The Command Center may fetch public GitHub repository/workflow metadata in the browser for currentness. Its committed `state.json` remains the durable fallback. Do not add GitHub credentials or private Site identifiers to client code.

## Privacy requirements

Keep the Site private. Preserve `noindex,nofollow,noarchive`. Do not expose owner identity, credentials, secrets, private project/deployment IDs, internal prompts, private comments, or billing/account identifiers. Authoritative aggregate interaction counts may be added later only through an approved private data source.

## Native Site verification

After publication, verify desktop and approximately 390 px small-screen rendering; inspect every section; confirm control links; confirm actual Refresh semantics; confirm public `ndaib` contains no Command Center navigation or link; and record the resulting private Site URL/version in a new durable publication receipt.

## Hard schedule constraint

Publishing this private Site does not authorize any schedule. The Command Center must continue to display planned 07:00/09:00 schedules as blocked, uncreated, and disabled until the old Daily AI Brief system is formally decommissioned.
