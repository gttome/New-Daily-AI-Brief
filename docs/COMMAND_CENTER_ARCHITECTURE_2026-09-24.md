# New Daily AI Brief Command Center — architecture

**Date:** 2026-09-24  
**Repository:** `gttome/New-Daily-AI-Brief`  
**Private Site identifier:** `npccs`

## Purpose

The Command Center is an owner-only operations surface over the existing canonical greenfield system. It observes durable state, explains the current publication condition, exposes safe manual entry points, and reports readiness. It does not contain an editorial engine, a publisher, a scheduler, or a second state machine.

## Authority boundary

The only Brief execution authority remains `.github/workflows/manual-daily-brief.yml` → `scripts/manual_canonical_run.py` → `start_daily_brief(...)` / the canonical `RunEngine`. Command Center controls are links/launch points into that existing workflow. Reader validation uses the existing `reader-parity.yml` workflow. Force Replace uses the existing workflow input and inherits its migrated-history protection through 2026-09-23.

The full Command Center must not be deployed on the public GitHub Pages reader preview. Its target is the separate private ChatGPT Site identified as `npccs`. The public `ndaib` reader is not modified by this implementation.

## Data contract

`scripts/build_command_center_snapshot.py` builds `site/command-center/state.json` from durable repository evidence. The schema is `schemas/command-center-state.schema.json`. The committed snapshot is a safe fallback; the browser may refresh public GitHub branch/workflow metadata for current run timing/status. If live metadata is unavailable, the UI keeps the durable snapshot and marks current live data unavailable.

The builder intentionally does not propagate Site project/version/deployment identifiers from publication receipts. It does not store credentials, tokens, internal prompts, owner identity, private comments, or billing identifiers. Unknown usage, credit, engagement, run-timing, and retry counts remain null/unavailable rather than estimated.

## Operational surfaces

The primary screen covers executive/today state, the 11 canonical stages, 2/2/2 story allocation and Agent Skills, image QA, media, Watchlist, book bridges, reader/Site QA, Critical/High defects, manual controls, production gates, schedule readiness, run performance, source health, incidents/recovery, usage/cost posture, and reader engagement where authoritative values exist.

Charts are derived only from authoritative GitHub Actions timestamps or durable source-status counts. No synthetic trend line is generated when the series is absent.

## Schedule safety

The Command Center contains no schedule-creation code. It displays the future 07:00 Publisher and 09:00 Validation/Repair plan with `created=false`, `enabled=false`, and `creation_permitted=false`. Formal old-system decommissioning is a prerequisite for any later schedule creation or activation.

## Refresh semantics

“Refresh state” fetches actual current GitHub metadata and updates the UI only when the fetch succeeds. It does not change the durable snapshot timestamp on failure and never substitutes the browser clock as evidence of a successful synchronization.

## Deployment boundary

Repository implementation and source QA can complete through GitHub. Publishing the full cockpit to the private ChatGPT Site requires an authorized native Sites surface. If that capability is absent in an implementation chat, publication must remain explicitly pending; public Pages is not an acceptable privacy workaround.
