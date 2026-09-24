"""Apply reviewed reader corrections without altering the historical snapshot."""
import json
import math
import hashlib
import re
import shutil
from pathlib import Path


def apply_reader_corrections(destination: Path, legacy: Path) -> dict:
    receipt = {"watchlist_root_path": False, "reading_estimates": [], "image_corrections": []}
    watchlist = destination / "assets/js/watchlist.js"
    if watchlist.exists():
        text = watchlist.read_text()
        old = "document.body.dataset.baseurl||'/Daily-AI-Brief'"
        if old in text:
            watchlist.write_text(text.replace(old, "document.body.dataset.baseurl??''"))
            receipt["watchlist_root_path"] = True
    edition_file = legacy / "_data/editions/2026-09-23.json"
    if edition_file.exists():
        edition = json.loads(edition_file.read_text())
        for story in edition.get("stories", []):
            evidence = story.get("source", {}).get("reading_evidence", {})
            words = evidence.get("word_count")
            if evidence.get("status") != "verified" or not isinstance(words, int) or words <= 0:
                continue
            relative = story["permanent_url"].strip("/")
            page = destination / relative / "index.html"
            if not page.exists():
                continue
            text = page.read_text()
            old = "Source reading time unavailable"
            if old in text:
                minutes = math.ceil(words / evidence.get("words_per_minute", 200))
                page.write_text(text.replace(old, f"Source article · about {minutes} min read"))
                receipt["reading_estimates"].append({"story_id": story["story_id"], "minutes": minutes})
    manifest_path = Path(__file__).resolve().parents[1] / "migration/reader-corrections/2026-09-23.json"
    if manifest_path.exists():
        if not edition_file.exists():
            raise ValueError("Image corrections require the authoritative September 23 edition")
        manifest = json.loads(manifest_path.read_text())
        stories = {s["story_id"]: s for s in edition["stories"]}
        for item in manifest["images"]:
            story = stories[item["story_id"]]
            original_path = story["image"]["path"]
            if item["quality_accepted"] is not True:
                raise ValueError("Image correction lacks visual acceptance")
            asset = manifest_path.parent / item["asset"]
            if asset.parent.resolve() != manifest_path.parent.resolve():
                raise ValueError("Image asset must be a sibling of its manifest")
            if hashlib.sha256(asset.read_bytes()).hexdigest() != item["sha256"]:
                raise ValueError("Corrected image digest mismatch")
            original_asset = destination / original_path
            if hashlib.sha256(original_asset.read_bytes()).hexdigest() != item["original_sha256"]:
                raise ValueError("Historical image bytes changed; reconcile before correction")
            corrected_path = str(Path(original_path).with_name(item["asset"]))
            shutil.copyfile(asset, destination / corrected_path)
            pattern = re.escape(original_path) + r"(?:\?v=[a-f0-9]+)?"
            for page in destination.rglob("*"):
                if page.is_file() and page.suffix in {".html", ".xml", ".json"}:
                    text = page.read_text()
                    updated = re.sub(pattern, corrected_path + "?v=" + item["sha256"][:16], text)
                    if text != updated:
                        page.write_text(updated)
            receipt["image_corrections"].append({"story_id": item["story_id"], "path": corrected_path, "sha256": item["sha256"], "original_retained": original_path})
    return receipt
