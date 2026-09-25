#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from new_daily_ai_brief.build import BuildStagePipeline
from new_daily_ai_brief.store import CanonicalStore, utc_now


def main() -> int:
    ap = argparse.ArgumentParser(description="Invalidate and rebuild only a locked canonical Watchlist artifact")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--state-root", required=True)
    ap.add_argument("--build-root", required=True)
    ap.add_argument("--receipt", required=True)
    args = ap.parse_args()

    store = CanonicalStore(Path(args.state_root), args.edition_date, "production")
    preserved_names = ("edition", "media", "book-bridges", "rating-contract")
    preserved_before = {}
    for name in preserved_names:
        record = store.load_artifact(name)
        if not record or record.get("status") != "locked":
            raise SystemExit(f"required preserved artifact is not locked: {name}")
        preserved_before[name] = record["content_digest"]

    prior = store.load_artifact("watchlist")
    if not prior or prior.get("status") != "locked":
        raise SystemExit("existing Watchlist must be locked before bounded repair")
    prior_digest = prior["content_digest"]
    invalidated = store.invalidate("watchlist", "2026-09-24 evidence-backed Watchlist repair")

    build = BuildStagePipeline(store, args.edition_date, Path(args.build_root))
    data = build.build_watchlist()
    artifact, reused = store.lock_artifact(
        artifact_type="watchlist",
        artifact_id=f"dab-{args.edition_date}-production:watchlist",
        data=data,
        produced_by_stage="building:watchlist-repair",
        input_digests=[preserved_before["edition"]],
    )
    if reused:
        raise SystemExit("Watchlist repair unexpectedly reused the stale artifact")

    preserved_after = {}
    for name in preserved_names:
        record = store.load_artifact(name)
        if not record or record.get("status") != "locked":
            raise SystemExit(f"preserved artifact lost lock during Watchlist repair: {name}")
        preserved_after[name] = record["content_digest"]
    if preserved_after != preserved_before:
        raise SystemExit("Watchlist repair modified a preserved editorial/media/book/rating artifact")

    run = store.load_run()
    if run:
        run.setdefault("stage_receipts", {})["watchlist_repair"] = {
            "repaired_at": utc_now(),
            "prior_watchlist_digest": prior_digest,
            "repaired_watchlist_digest": artifact["content_digest"],
            "preserved_artifact_digests": preserved_after,
        }
        store.write_run(run)

    receipt = {
        "schema_version": "1.0.0",
        "edition_date": args.edition_date,
        "repaired_at": utc_now(),
        "invalidated_artifacts": invalidated,
        "prior_watchlist_digest": prior_digest,
        "repaired_watchlist_digest": artifact["content_digest"],
        "counts": artifact["data"]["counts"],
        "preserved_artifact_digests": preserved_after,
        "stories_images_videos_podcasts_redone": False,
    }
    path = Path(args.receipt)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
