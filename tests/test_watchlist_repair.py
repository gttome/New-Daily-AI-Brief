from __future__ import annotations

import json
import unittest
from copy import deepcopy
from pathlib import Path

from new_daily_ai_brief.watchlist_live import (
    prepare_watchlist_inputs,
    validate_public_watchlist,
    validate_review,
)


ROOT = Path(__file__).resolve().parents[1]


class WatchlistRepairTests(unittest.TestCase):
    DATE = "2026-09-24"

    def prior(self):
        return {
            "edition_date": "2026-09-23",
            "topics": [
                {
                    "topic_id": "topic-a",
                    "name": "Agent harness engineering",
                    "summary": "Harnesses coordinate tools and checks.",
                    "status": "early_signal",
                    "first_detected": "2026-09-22T12:00:00Z",
                    "updated_at": "2026-09-23T12:00:00Z",
                    "evidence": [{
                        "title": "Prior source",
                        "url": "https://example.com/prior",
                        "publisher": "Example",
                        "publication_date": "2026-09-23",
                        "checked_at": "2026-09-23T12:00:00Z",
                    }],
                }
            ],
        }

    def review(self):
        return {
            "edition_date": self.DATE,
            "checked_at": "2026-09-24T12:00:00-05:00",
            "review_complete": True,
            "policy": {
                "new_topic_min_independent_sources": 2,
                "zero_new_min_candidates_reviewed": 3,
            },
            "source_checks": [{
                "source_id": "primary-a",
                "status": "retrieved",
                "topic_ids": ["topic-a"],
            }],
            "updated_topics": [{
                "topic_id": "topic-a",
                "material_change": "A new primary source adds a concrete harness implementation.",
                "evidence": [{
                    "title": "New source",
                    "url": "https://example.com/new",
                    "publisher": "Primary A",
                    "source_id": "primary-a",
                    "publication_date": "2026-09-24",
                    "checked_at": "2026-09-24T12:00:00-05:00",
                    "qualifies_for_daily_state": True,
                }],
            }],
            "new_topics": [],
            "zero_new_certified": True,
            "candidate_dispositions": [
                {"name": "a", "disposition": "update_existing"},
                {"name": "b", "disposition": "needs_research"},
                {"name": "c", "disposition": "needs_research"},
            ],
        }

    def test_story_overlap_alone_cannot_mark_topic_updated(self):
        review = self.review()
        review["updated_topics"] = []
        registry, catalog, manifest = prepare_watchlist_inputs(self.DATE, self.prior(), review)
        self.assertEqual(manifest["updated_today"], [])
        self.assertEqual(manifest["carried_forward"], ["topic-a"])
        self.assertNotIn("story", manifest["method"])
        self.assertEqual(len(registry["sources"]), 2)
        self.assertEqual(catalog["topics"][0]["last_changed"], "2026-09-23")

    def test_updated_topic_requires_new_current_date_evidence(self):
        review = self.review()
        review["updated_topics"][0]["evidence"][0]["checked_at"] = "2026-09-23T23:59:00Z"
        with self.assertRaisesRegex(ValueError, "current-date evidence"):
            validate_review(review, self.DATE, self.prior())

    def test_updated_topic_cannot_reuse_prior_evidence_url(self):
        review = self.review()
        review["updated_topics"][0]["evidence"][0]["url"] = "https://example.com/prior"
        with self.assertRaisesRegex(ValueError, "no new evidence URL"):
            validate_review(review, self.DATE, self.prior())

    def test_new_topic_requires_independent_evidence_threshold(self):
        review = self.review()
        review["zero_new_certified"] = False
        review["new_topics"] = [{
            "topic": {
                "topic_id": "topic-new",
                "name": "New topic",
                "summary": "New signal",
                "status": "early_signal",
            },
            "rationale": "Two independent original sources establish the signal.",
            "evidence": [{
                "title": "Only source",
                "url": "https://example.com/one",
                "publisher": "One",
                "publication_date": "2026-09-24",
                "checked_at": "2026-09-24T12:00:00-05:00",
                "qualifies_for_daily_state": True,
            }],
        }]
        with self.assertRaisesRegex(ValueError, "independent-evidence threshold"):
            validate_review(review, self.DATE, self.prior())

    def test_public_reader_rejects_prior_day_watchlist(self):
        canonical = {
            "edition_date": self.DATE,
            "status": "locked",
            "content_digest": "sha256:" + "a" * 64,
            "data": {"counts": {"new_today": 0, "updated_today": 0, "carried_forward": 1}},
        }
        stale = deepcopy(self.prior())
        stale["canonical_watchlist_digest"] = canonical["content_digest"]
        with self.assertRaisesRegex(ValueError, "stale or mismatched"):
            validate_public_watchlist(stale, canonical, self.DATE)

    def test_public_reader_rejects_digest_mismatch(self):
        public = {
            "edition_date": self.DATE,
            "canonical_watchlist_digest": "sha256:" + "b" * 64,
            "counts": {"new_today": 0, "updated_today": 0, "carried_forward": 0},
            "topics": [],
        }
        canonical = {
            "edition_date": self.DATE,
            "status": "locked",
            "content_digest": "sha256:" + "a" * 64,
            "data": {"counts": {"new_today": 0, "updated_today": 0, "carried_forward": 0}},
        }
        with self.assertRaisesRegex(ValueError, "digest"):
            validate_public_watchlist(public, canonical, self.DATE)

    def test_september_24_repair_counts_are_0_3_13(self):
        prior_path = ROOT / "legacy_snapshot" / "_data" / "watchlist.json"
        review_path = ROOT / "evidence" / "watchlist" / "2026-09-24-review.json"
        if not prior_path.exists():
            self.skipTest("legacy snapshot not initialized")
        prior = json.loads(prior_path.read_text(encoding="utf-8"))
        review = json.loads(review_path.read_text(encoding="utf-8"))
        _, _, manifest = prepare_watchlist_inputs(self.DATE, prior, review)
        self.assertEqual(len(manifest["new_today"]), 0)
        self.assertEqual(len(manifest["updated_today"]), 3)
        self.assertEqual(len(manifest["carried_forward"]), 13)

    def test_repair_workflow_reuses_validated_publication_stage(self):
        workflow = (ROOT / ".github" / "workflows" / "repair-sep24-watchlist.yml").read_text(encoding="utf-8")
        self.assertIn(".repair-artifact/.publication-stage", workflow)
        repair_block = workflow.split("- name: Reassemble only affected live reader output", 1)[1].split("- name: Build and validate Site-ready repaired reader", 1)[0]
        self.assertNotIn("build_live_edition.py", repair_block)
        self.assertNotIn("_generator/cli.mjs", repair_block)

    def test_greenfield_watchlist_presentation_is_owned(self):
        page = (ROOT / "migration" / "watchlist-current" / "watchlist" / "index.md").read_text(encoding="utf-8")
        js = (ROOT / "migration" / "watchlist-current" / "assets" / "js" / "watchlist.js").read_text(encoding="utf-8")
        self.assertIn('data-watchlist-contract="greenfield-watchlist-v1"', page)
        self.assertIn("new today ·", js)
        self.assertIn("wl-preview-summary", js)


if __name__ == "__main__":
    unittest.main()
