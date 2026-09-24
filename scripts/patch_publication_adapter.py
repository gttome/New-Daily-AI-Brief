#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

OLD = """      const age=(Date.parse(edition.brief_date)-Date.parse(podcast.publication_date))/86400000;
      if(!Number.isFinite(age)||age<0||age>PODCAST_EXCEPTION_AGE_DAYS)errors.push(`${label} exceeds the ${PODCAST_EXCEPTION_AGE_DAYS}-day absolute freshness ceiling`);
      else if(age>PODCAST_PRIMARY_AGE_DAYS){
        requireText(podcast.freshness_exception_reason,`${label}.freshness_exception_reason`);
        const expectedTier=age<=PODCAST_FALLBACK_AGE_DAYS?'fallback_7d':'exception_30d';
        if(podcast.freshness_tier!==expectedTier)errors.push(`${label}.freshness_tier must be ${expectedTier}`);
      }else if(podcast.freshness_tier&&podcast.freshness_tier!=='primary_48h')errors.push(`${label}.freshness_tier must be primary_48h inside the primary window`);
"""

NEW = """      const published=time(podcast.published_at||podcast.publication_date);
      const podcastCutoff=Number.isFinite(cutoff)?cutoff:time(`${edition.brief_date}T23:59:59Z`);
      const ageHours=(podcastCutoff-published)/3600000;
      if(!Number.isFinite(ageHours)||ageHours<0||ageHours>PODCAST_EXCEPTION_AGE_DAYS*24)errors.push(`${label} exceeds the ${PODCAST_EXCEPTION_AGE_DAYS}-day absolute freshness ceiling`);
      else if(ageHours>PODCAST_PRIMARY_AGE_DAYS*24){
        requireText(podcast.freshness_exception_reason,`${label}.freshness_exception_reason`);
        const expectedTier=ageHours<=PODCAST_FALLBACK_AGE_DAYS*24?'fallback_7d':'exception_30d';
        if(podcast.freshness_tier!==expectedTier)errors.push(`${label}.freshness_tier must be ${expectedTier}`);
      }else if(podcast.freshness_tier&&podcast.freshness_tier!=='primary_48h')errors.push(`${label}.freshness_tier must be primary_48h inside the primary window`);
"""

def main() -> int:
    ap = argparse.ArgumentParser(description="Patch pinned publication adapter to validate podcast freshness using verified timestamps.")
    ap.add_argument("--adapter-root", required=True)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()

    path = Path(args.adapter_root) / "_generator" / "lib" / "validate.mjs"
    text = path.read_text(encoding="utf-8")
    if NEW in text:
        print(f"{path}: timestamp freshness patch already present")
        return 0
    if OLD not in text:
        raise SystemExit(f"{path}: expected pinned validator block not found; refusing unguarded patch")
    if args.check:
        print(f"{path}: pinned validator is compatible with timestamp freshness patch")
        return 0
    path.write_text(text.replace(OLD, NEW, 1), encoding="utf-8")
    print(f"{path}: applied timestamp freshness patch")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
