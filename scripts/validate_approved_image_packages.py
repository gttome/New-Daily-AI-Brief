#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def main() -> int:
    root = Path("approved-images")
    if not root.exists():
        print("approved-images directory not present; nothing to validate")
        return 0

    manifests = sorted(root.glob("*/approved-image-manifest.json"))
    for manifest_path in manifests:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        images = manifest.get("images")
        if not isinstance(images, list) or len(images) != 6:
            raise SystemExit(f"{manifest_path}: exactly six images required")
        digests: set[str] = set()
        for entry in images:
            if entry.get("quality_accepted") is not True or entry.get("accepted_locked") is not True:
                raise SystemExit(f"{manifest_path}: image is not accepted/locked")
            if entry.get("generation_method") != "openai_image_generation":
                raise SystemExit(f"{manifest_path}: invalid generation_method")
            rel = str(entry.get("file") or "")
            path = Path(rel)
            if not path.is_file():
                raise SystemExit(f"{manifest_path}: missing image {rel}")
            if path.suffix.lower() not in {".webp", ".png"}:
                raise SystemExit(f"{manifest_path}: invalid image format {rel}")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != str(entry.get("sha256") or ""):
                raise SystemExit(f"{manifest_path}: sha256 mismatch {rel}")
            digests.add(digest)
        if len(digests) != 6:
            raise SystemExit(f"{manifest_path}: images must have six distinct byte streams")
        print(f"{manifest_path}: approved image package PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
