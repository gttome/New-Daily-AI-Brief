#!/usr/bin/env python3
from __future__ import annotations

import argparse
import email.utils
import html
import json
import re
import ssl
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

USER_AGENT = "New-Daily-AI-Brief-live-media/1.0 (+https://github.com/gttome/New-Daily-AI-Brief)"
STOP = {
    "about","after","again","agent","agents","with","from","into","that","this","their","there",
    "using","your","have","more","than","what","when","where","which","while","will","today",
    "new","adds","available","generative","artificial","intelligence"
}
AGENT_TERMS = {"agent","agents","agentic","skill","skills","harness","workflow","workflows","copilot","codex","automation"}


def load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def clean(value: Any, limit: int = 500) -> str:
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip() + "…"


def http_text(url: str, timeout: int = 18, attempts: int = 2) -> tuple[str, str, int]:
    last: Exception | None = None
    for attempt in range(attempts):
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept": "text/html,application/rss+xml,application/atom+xml,application/xml;q=0.9,*/*;q=0.7",
                },
            )
            with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as response:
                body = response.read(2_500_000)
                return body.decode("utf-8", errors="replace"), response.geturl(), int(response.status)
        except Exception as exc:  # noqa: BLE001
            last = exc
            if attempt + 1 < attempts:
                time.sleep(0.5)
    raise RuntimeError(f"retrieval_failed:{type(last).__name__}:{last}")


def parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        pass
    try:
        dt = email.utils.parsedate_to_datetime(text)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def terms_from_editorial(catalog: dict[str, Any]) -> set[str]:
    terms: set[str] = set()
    for item in catalog.get("candidates", []):
        text = " ".join(str(item.get(k, "")) for k in ("title", "summary", "why_it_matters")).lower()
        for token in re.findall(r"[a-z0-9][a-z0-9-]{3,}", text):
            if token not in STOP:
                terms.add(token)
    return terms


def overlap_score(title: str, description: str, editorial_terms: set[str]) -> int:
    text = f"{title} {description}".lower()
    words = set(re.findall(r"[a-z0-9][a-z0-9-]{3,}", text))
    return len(words & editorial_terms) * 5 + sum(2 for term in AGENT_TERMS if term in words)


def extract_channel_id(page: str) -> str | None:
    patterns = (
        r'"channelId"\s*:\s*"(UC[a-zA-Z0-9_-]{20,})"',
        r'"externalId"\s*:\s*"(UC[a-zA-Z0-9_-]{20,})"',
        r'<meta\s+itemprop="channelId"\s+content="(UC[a-zA-Z0-9_-]{20,})"',
    )
    for pattern in patterns:
        match = re.search(pattern, page)
        if match:
            return match.group(1)
    return None


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def child_text(node: ET.Element, names: set[str]) -> str | None:
    for child in node.iter():
        if child is node:
            continue
        if local_name(child.tag) in names and child.text and child.text.strip():
            return child.text.strip()
    return None


def entry_link(node: ET.Element) -> str | None:
    for child in node.iter():
        if local_name(child.tag) != "link":
            continue
        href = child.attrib.get("href")
        rel = child.attrib.get("rel", "alternate")
        if href and rel in {"alternate", ""}:
            return href.strip()
        if child.text and child.text.strip().startswith("http"):
            return child.text.strip()
    return None


def parse_feed(xml_text: str) -> list[dict[str, Any]]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise RuntimeError(f"feed_parse_failed:{exc}") from exc
    nodes = [x for x in root.iter() if local_name(x.tag) in {"item", "entry"}]
    out: list[dict[str, Any]] = []
    for node in nodes:
        title = child_text(node, {"title"})
        link = entry_link(node)
        published = child_text(node, {"published", "pubdate", "updated", "date"})
        description = child_text(node, {"description", "summary", "content", "encoded"})
        duration = child_text(node, {"duration"})
        if not title or not link:
            continue
        out.append(
            {
                "title": clean(title, 240),
                "url": urllib.parse.urljoin(link, link),
                "published_raw": published,
                "description": clean(description, 700),
                "duration_raw": duration,
            }
        )
    return out


def parse_duration(value: str | None) -> int | None:
    if not value:
        return None
    text = value.strip()
    if text.isdigit():
        return int(text)
    parts = text.split(":")
    try:
        nums = [int(x) for x in parts]
    except ValueError:
        return None
    if len(nums) == 2:
        return nums[0] * 60 + nums[1]
    if len(nums) == 3:
        return nums[0] * 3600 + nums[1] * 60 + nums[2]
    return None


def youtube_runtime(url: str) -> int | None:
    text, _, _ = http_text(url)
    for pattern in (
        r'"lengthSeconds"\s*:\s*"?(\d+)"?',
        r'"approxDurationMs"\s*:\s*"?(\d+)"?',
    ):
        match = re.search(pattern, text)
        if match:
            raw = int(match.group(1))
            return raw // 1000 if "DurationMs" in pattern else raw
    return None


def discover_videos(config: dict[str, Any], cutoff: datetime, editorial_terms: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    policy = config["video_policy"]
    max_age = float(policy["max_age_hours"])
    max_entries = int(policy["max_entries_per_source"])
    diagnostics: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for source in sorted(config["video_sources"], key=lambda x: (int(x["priority"]), x["source_id"])):
        record = {"source_id": source["source_id"], "kind": "video", "status": "unavailable", "candidates": 0}
        try:
            channel_html, resolved, _ = http_text(source["channel_url"])
            channel_id = extract_channel_id(channel_html)
            if not channel_id:
                raise RuntimeError("channel_id_not_found")
            feed_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            feed_text, _, _ = http_text(feed_url)
            entries = parse_feed(feed_text)[:max_entries]
            record.update({"status": "retrieved", "channel_id": channel_id, "feed_url": feed_url, "resolved_channel_url": resolved})
            for entry in entries:
                published = parse_date(entry["published_raw"])
                if not published:
                    continue
                age_hours = (cutoff - published.astimezone(timezone.utc)).total_seconds() / 3600
                if age_hours < 0 or age_hours > max_age:
                    continue
                runtime = None
                try:
                    runtime = youtube_runtime(entry["url"])
                except Exception as exc:  # noqa: BLE001
                    record.setdefault("runtime_failures", []).append({"url": entry["url"], "reason": str(exc)})
                if runtime is None or runtime < 1 or runtime > int(policy["absolute_max_runtime_seconds"]):
                    continue
                preferred = runtime <= int(policy["preferred_max_runtime_seconds"])
                score = overlap_score(entry["title"], entry["description"], editorial_terms)
                score += 35 if preferred else 15
                score += max(0, int(24 - min(age_hours, 24)))
                candidates.append(
                    {
                        "kind": "video",
                        "source_id": source["source_id"],
                        "channel": source["name"],
                        "title": entry["title"],
                        "url": entry["url"],
                        "published_at": published.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "publication_date": published.date().isoformat(),
                        "runtime_seconds": runtime,
                        "duration_tier": "short" if preferred else ("fallback" if runtime <= 900 else "last_resort"),
                        "description": entry["description"],
                        "agent_signal": any(term in f"{entry['title']} {entry['description']}".lower() for term in AGENT_TERMS),
                        "score": score,
                        "available": True,
                    }
                )
            record["candidates"] = sum(1 for x in candidates if x["source_id"] == source["source_id"])
        except Exception as exc:  # noqa: BLE001
            record["reason"] = str(exc)
        diagnostics.append(record)

    candidates.sort(key=lambda x: (-int(x["score"]), x["published_at"], x["url"]))
    selected: list[dict[str, Any]] = []
    agent = next((x for x in candidates if x["agent_signal"]), None)
    if agent:
        selected.append(agent)
    for candidate in candidates:
        if len(selected) >= int(policy["target_count"]):
            break
        if candidate["url"] in {x["url"] for x in selected}:
            continue
        if selected and candidate["source_id"] == selected[0]["source_id"]:
            alternative = next(
                (
                    x for x in candidates
                    if x["url"] not in {y["url"] for y in selected}
                    and x["source_id"] != selected[0]["source_id"]
                ),
                None,
            )
            if alternative:
                continue
        selected.append(candidate)
    if len(selected) < int(policy["target_count"]):
        for candidate in candidates:
            if len(selected) >= int(policy["target_count"]):
                break
            if candidate["url"] not in {x["url"] for x in selected}:
                selected.append(candidate)
    if len(selected) != int(policy["target_count"]):
        raise SystemExit(f"live video discovery produced {len(selected)} verified candidates; exactly {policy['target_count']} required")
    for candidate in selected:
        try:
            _, resolved, status = http_text(candidate["url"])
            candidate["reachable"] = 200 <= status < 400
            candidate["http_status"] = status
            candidate["resolved_url"] = resolved
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"selected video URL failed final reachability verification: {candidate['url']}: {exc}") from exc
    return selected, diagnostics


def autodiscover_feed(website: str) -> tuple[str, str]:
    page, resolved, _ = http_text(website)
    patterns = (
        r'<link\b[^>]*type=["\']application/(?:rss|atom)\+xml["\'][^>]*href=["\']([^"\']+)["\']',
        r'<link\b[^>]*href=["\']([^"\']+)["\'][^>]*type=["\']application/(?:rss|atom)\+xml["\']',
    )
    for pattern in patterns:
        match = re.search(pattern, page, re.I)
        if match:
            return urllib.parse.urljoin(resolved, html.unescape(match.group(1))), resolved
    candidates = re.findall(r'href=["\']([^"\']+(?:feed|rss)[^"\']*)["\']', page, re.I)
    for candidate in candidates[:8]:
        url = urllib.parse.urljoin(resolved, html.unescape(candidate))
        if url.startswith("http"):
            return url, resolved
    raise RuntimeError("rss_autodiscovery_failed")


def discover_podcasts(config: dict[str, Any], cutoff: datetime, editorial_terms: set[str], excluded_urls: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    policy = config["podcast_policy"]
    diagnostics: list[dict[str, Any]] = []
    candidates: list[dict[str, Any]] = []
    for source in sorted(config["podcast_sources"], key=lambda x: (int(x["priority"]), x["source_id"])):
        record = {"source_id": source["source_id"], "kind": "podcast", "status": "unavailable", "candidates": 0}
        try:
            feed_url = source.get("feed_url")
            website_resolved = source["website"]
            if not feed_url:
                feed_url, website_resolved = autodiscover_feed(source["website"])
            feed_text, resolved_feed, _ = http_text(feed_url)
            entries = parse_feed(feed_text)[: int(policy["max_entries_per_source"])]
            record.update({"status": "retrieved", "feed_url": resolved_feed, "website_url": website_resolved})
            for entry in entries:
                published = parse_date(entry["published_raw"])
                if not published:
                    continue
                age_hours = (cutoff - published.astimezone(timezone.utc)).total_seconds() / 3600
                if age_hours < 0 or age_hours > float(policy["absolute_max_age_days"]) * 24:
                    continue
                if entry["url"] in excluded_urls:
                    continue
                if age_hours <= float(policy["primary_max_age_hours"]):
                    freshness_tier = "primary_48h"
                    freshness_bonus = 35
                    exception = None
                elif age_hours <= float(policy["fallback_max_age_days"]) * 24:
                    freshness_tier = "fallback_7d"
                    freshness_bonus = 18
                    exception = "No second sufficiently relevant verified episode from a distinct source qualified inside the preferred 48-hour window."
                else:
                    freshness_tier = "exception_30d"
                    freshness_bonus = 5
                    exception = "No second sufficiently relevant verified episode from a distinct source qualified inside the seven-day fallback window."
                runtime = parse_duration(entry["duration_raw"])
                score = overlap_score(entry["title"], entry["description"], editorial_terms) + freshness_bonus
                candidates.append(
                    {
                        "kind": "podcast",
                        "source_id": source["source_id"],
                        "show": source["show"],
                        "host": source["show"],
                        "title": entry["title"],
                        "url": entry["url"],
                        "publisher_url": website_resolved,
                        "published_at": published.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "publication_date": published.date().isoformat(),
                        "runtime_seconds": runtime,
                        "description": entry["description"],
                        "freshness_tier": freshness_tier,
                        "freshness_exception_reason": exception,
                        "score": score,
                        "available": True,
                    }
                )
            record["candidates"] = sum(1 for x in candidates if x["source_id"] == source["source_id"])
        except Exception as exc:  # noqa: BLE001
            record["reason"] = str(exc)
        diagnostics.append(record)

    candidates.sort(key=lambda x: (-int(x["score"]), x["published_at"], x["url"]))
    selected: list[dict[str, Any]] = []
    for candidate in candidates:
        if candidate["source_id"] in {x["source_id"] for x in selected}:
            continue
        selected.append(candidate)
        if len(selected) >= int(policy["target_count"]):
            break
    if len(selected) != int(policy["target_count"]):
        raise SystemExit(f"live podcast discovery produced {len(selected)} source-diverse verified candidates; exactly {policy['target_count']} required")
    for candidate in selected:
        try:
            _, resolved, status = http_text(candidate["url"])
            candidate["reachable"] = 200 <= status < 400
            candidate["http_status"] = status
            candidate["resolved_url"] = resolved
        except Exception as exc:  # noqa: BLE001
            raise SystemExit(f"selected podcast URL failed final reachability verification: {candidate['url']}: {exc}") from exc
    return selected, diagnostics


def main() -> int:
    ap = argparse.ArgumentParser(description="Zero-paid-API discovery for Daily AI Brief videos and podcasts")
    ap.add_argument("--edition-date", required=True)
    ap.add_argument("--editorial-catalog", required=True)
    ap.add_argument("--config", default="config/live-media-sources.json")
    ap.add_argument("--output", required=True)
    ap.add_argument("--cutoff", default="")
    args = ap.parse_args()

    editorial = load(Path(args.editorial_catalog))
    config = load(Path(args.config))
    cutoff = parse_date(args.cutoff) if args.cutoff else datetime.now(timezone.utc)
    if cutoff is None:
        raise SystemExit("invalid cutoff")
    if cutoff.date().isoformat() < args.edition_date:
        raise SystemExit("cutoff precedes edition date")

    editorial_terms = terms_from_editorial(editorial)
    videos, video_diag = discover_videos(config, cutoff, editorial_terms)
    podcasts, podcast_diag = discover_podcasts(config, cutoff, editorial_terms, {x["url"] for x in videos})

    result = {
        "schema_version": "1.0.0",
        "edition_date": args.edition_date,
        "cutoff": cutoff.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "execution_owner": "github_actions",
        "paid_api_calls": 0,
        "selection_policy": {
            "videos": config["video_policy"],
            "podcasts": config["podcast_policy"],
        },
        "selected": {"videos": videos, "podcasts": podcasts},
        "diagnostics": {"video_sources": video_diag, "podcast_sources": podcast_diag},
        "ready": len(videos) == 2 and len(podcasts) == 2,
    }
    dump(Path(args.output), result)
    print(json.dumps({
        "edition_date": args.edition_date,
        "videos": len(videos),
        "podcasts": len(podcasts),
        "paid_api_calls": 0,
        "ready": result["ready"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
