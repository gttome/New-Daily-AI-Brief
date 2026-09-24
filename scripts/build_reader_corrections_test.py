"""Bounded regression checks for the observed September 23 reader defects."""
import json
import shutil
import tempfile
from pathlib import Path
from build_reader_corrections import apply_reader_corrections

legacy = Path("legacy_snapshot")
edition = json.loads((legacy / "_data/editions/2026-09-23.json").read_text())
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    js = root / "assets/js/watchlist.js"
    js.parent.mkdir(parents=True)
    js.write_text("const base=document.body.dataset.baseurl||'/Daily-AI-Brief';")
    for story in edition["stories"]:
        page = root / story["permanent_url"].strip("/") / "index.html"
        page.parent.mkdir(parents=True)
        page.write_text('Source reading time unavailable <img src="/' + story["image"]["path"] + '">')
        image = root / story["image"]["path"]
        image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(legacy / story["image"]["path"], image)
    result = apply_reader_corrections(root, legacy)
    assert result["watchlist_root_path"] is True
    assert "??''" in js.read_text()
    assert len(result["reading_estimates"]) == 6
    assert len(result["image_corrections"]) == 3
    for row in result["image_corrections"]:
        original = root / row["original_retained"]
        assert original.read_bytes() == (legacy / row["original_retained"]).read_bytes()
        story = next(s for s in edition["stories"] if s["story_id"] == row["story_id"])
        page = root / story["permanent_url"].strip("/") / "index.html"
        assert row["path"] in page.read_text()
        assert "Source reading time unavailable" not in page.read_text()
    # A changed historical image must never silently receive a mismatched correction.
    (root / result["image_corrections"][0]["original_retained"]).write_bytes(b"corrupt")
    try:
        apply_reader_corrections(root, legacy)
    except ValueError as error:
        assert "Historical image bytes changed" in str(error)
    else:
        raise AssertionError("Corrupt source image was accepted")
print("Reader correction regression checks passed")
