from __future__ import annotations

from copy import deepcopy
from typing import Any
from urllib.parse import urlsplit

ARCHIVED = {"archived", "retired", "inactive"}
ALLOWED_SOURCE_STATUSES = {
    "retrieved", "no_candidate_links", "unavailable", "assisted_review_required", "not_due"
}


def _day(value: Any) -> str:
    return str(value or "")[:10]


def _https(url: str) -> bool:
    try:
        parts = urlsplit(url)
        return parts.scheme == "https" and bool(parts.netloc)
    except Exception:
        return False


def topic_is_active(topic: dict[str, Any]) -> bool:
    return str(topic.get("status") or "").lower() not in ARCHIVED


def daily_state(topic: dict[str, Any], edition_date: str) -> str:
    first = _day(topic.get("first_detected") or topic.get("first_seen"))
    changed = _day(topic.get("updated_at") or topic.get("last_changed") or first)
    if first == edition_date:
        return "new_today"
    if changed == edition_date:
        return "updated_today"
    return "carried_forward"


def _qualifying_evidence(entry: dict[str, Any], edition_date: str) -> bool:
    if not _https(str(entry.get("url") or "")):
        return False
    if not str(entry.get("title") or "").strip() or not str(entry.get("publisher") or "").strip():
        return False
    if _day(entry.get("checked_at")) != edition_date:
        return False
    published = _day(entry.get("publication_date"))
    if published and published > edition_date:
        return False
    return entry.get("qualifies_for_daily_state", True) is True


def validate_review(review: dict[str, Any], edition_date: str, prior: dict[str, Any]) -> dict[str, Any]:
    if review.get("edition_date") != edition_date:
        raise ValueError("Watchlist review edition_date does not match the Brief date")
    if review.get("review_complete") is not True:
        raise ValueError("Watchlist review must be explicitly complete")
    if _day(review.get("checked_at")) != edition_date:
        raise ValueError("Watchlist review checked_at must be on the Brief date")

    source_checks = review.get("source_checks") or []
    if not source_checks:
        raise ValueError("Watchlist review requires source check receipts")
    for row in source_checks:
        if row.get("status") not in ALLOWED_SOURCE_STATUSES:
            raise ValueError(f"unsupported Watchlist source status: {row.get('status')}")
        if not row.get("source_id"):
            raise ValueError("Watchlist source check is missing source_id")

    prior_topics = {str(t.get("topic_id")): t for t in prior.get("topics") or []}
    updates = review.get("updated_topics") or []
    seen: set[str] = set()
    prior_urls = {
        topic_id: {str(e.get("url")) for e in (topic.get("evidence") or []) if e.get("url")}
        for topic_id, topic in prior_topics.items()
    }
    for row in updates:
        topic_id = str(row.get("topic_id") or "")
        if topic_id in seen or topic_id not in prior_topics:
            raise ValueError(f"invalid or duplicate updated topic: {topic_id}")
        seen.add(topic_id)
        if not topic_is_active(prior_topics[topic_id]):
            raise ValueError(f"inactive topic cannot be updated_today: {topic_id}")
        evidence = row.get("evidence") or []
        if not evidence or not all(_qualifying_evidence(e, edition_date) for e in evidence):
            raise ValueError(f"updated topic lacks qualifying current-date evidence: {topic_id}")
        if not str(row.get("material_change") or "").strip():
            raise ValueError(f"updated topic lacks material-change rationale: {topic_id}")
        if not any(str(e.get("url")) not in prior_urls[topic_id] for e in evidence):
            raise ValueError(f"updated topic has no new evidence URL: {topic_id}")

    policy = review.get("policy") or {}
    new_min = int(policy.get("new_topic_min_independent_sources") or 2)
    new_topics = review.get("new_topics") or []
    new_ids: set[str] = set()
    for row in new_topics:
        topic = row.get("topic") or {}
        topic_id = str(topic.get("topic_id") or "")
        if not topic_id or topic_id in prior_topics or topic_id in new_ids:
            raise ValueError(f"invalid or duplicate new Watchlist topic: {topic_id}")
        new_ids.add(topic_id)
        evidence = row.get("evidence") or topic.get("evidence") or []
        qualifying = [e for e in evidence if _qualifying_evidence(e, edition_date)]
        independent = {str(e.get("publisher") or "").strip().lower() for e in qualifying}
        if len(qualifying) < new_min or len(independent) < new_min:
            raise ValueError(f"new topic does not meet the independent-evidence threshold: {topic_id}")
        if not str(row.get("rationale") or "").strip():
            raise ValueError(f"new topic lacks research rationale: {topic_id}")

    if not new_topics:
        if review.get("zero_new_certified") is not True:
            raise ValueError("zero-new Watchlist result is not certified")
        dispositions = review.get("candidate_dispositions") or []
        if len(dispositions) < int(policy.get("zero_new_min_candidates_reviewed") or 3):
            raise ValueError("zero-new certification requires at least three reviewed candidate concepts")

    return {
        "updated_count": len(updates),
        "new_count": len(new_topics),
        "source_check_count": len(source_checks),
        "new_topic_min_independent_sources": new_min,
    }


def prepare_watchlist_inputs(
    edition_date: str,
    prior: dict[str, Any],
    review: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    validation = validate_review(review, edition_date, prior)
    checked_at = str(review["checked_at"])
    updates = {str(x["topic_id"]): x for x in review.get("updated_topics") or []}
    prior_topics = prior.get("topics") or []
    topics: list[dict[str, Any]] = []

    for position, original in enumerate(prior_topics, start=1):
        topic = deepcopy(original)
        topic_id = str(topic["topic_id"])
        first_seen = _day(topic.get("first_detected") or topic.get("first_seen") or edition_date)
        last_changed = _day(topic.get("updated_at") or topic.get("last_changed") or first_seen)
        qualifying: list[dict[str, Any]] = []
        if topic_id in updates:
            change = updates[topic_id]
            qualifying = deepcopy(change.get("evidence") or [])
            existing_urls = {str(e.get("url")) for e in topic.get("evidence") or [] if e.get("url")}
            for evidence in qualifying:
                if str(evidence.get("url")) not in existing_urls:
                    topic.setdefault("evidence", []).append(deepcopy(evidence))
                    existing_urls.add(str(evidence.get("url")))
            topic["updated_at"] = checked_at
            topic["daily_change_note"] = change["material_change"]
            last_changed = edition_date
        topics.append({
            "topic_id": topic_id,
            "title": topic.get("name") or topic_id,
            "summary": topic.get("summary") or topic.get("why_now") or "Carried forward from the verified Emerging AI Watchlist.",
            "first_seen": first_seen,
            "last_changed": last_changed,
            "active": topic_is_active(topic),
            "presentation_order": position,
            "public_topic": topic,
            "qualifying_evidence": qualifying,
        })

    for row in review.get("new_topics") or []:
        topic = deepcopy(row["topic"])
        topic_id = str(topic["topic_id"])
        evidence = deepcopy(row.get("evidence") or topic.get("evidence") or [])
        topic["evidence"] = evidence
        topic.setdefault("first_detected", checked_at)
        topic["updated_at"] = checked_at
        topic["daily_change_note"] = row["rationale"]
        topics.append({
            "topic_id": topic_id,
            "title": topic.get("name") or topic_id,
            "summary": topic.get("summary") or topic.get("why_now") or "Newly verified Watchlist topic.",
            "first_seen": edition_date,
            "last_changed": edition_date,
            "active": topic_is_active(topic),
            "presentation_order": len(topics) + 1,
            "public_topic": topic,
            "qualifying_evidence": evidence,
        })

    all_ids = [x["topic_id"] for x in topics]
    registry_sources = [{
        "source_id": "prior-canonical-watchlist-baseline",
        "priority": 1,
        "topic_ids": all_ids,
    }]
    for idx, check in enumerate(review.get("source_checks") or [], start=1):
        related = list(check.get("topic_ids") or [])
        registry_sources.append({
            "source_id": f"live-review-{check['source_id']}",
            "priority": 10 + idx,
            "topic_ids": sorted(set(str(x) for x in related if x)),
        })

    counts = {"new_today": 0, "updated_today": 0, "carried_forward": 0}
    for item in topics:
        if item["active"]:
            counts[daily_state(item["public_topic"], edition_date)] += 1

    registry = {"schema_version": "1.0.0", "sources": registry_sources}
    catalog = {
        "schema_version": "1.0.0",
        "edition_date": edition_date,
        "reviewed_at": checked_at,
        "baseline_note": review.get("baseline_note") or (
            f"{edition_date} Watchlist review: {counts['new_today']} new today, "
            f"{counts['updated_today']} updated today, {counts['carried_forward']} carried forward."
        ),
        "review_policy": deepcopy(review.get("policy") or {}),
        "source_checks": deepcopy(review.get("source_checks") or []),
        "candidate_dispositions": deepcopy(review.get("candidate_dispositions") or []),
        "topics": topics,
    }
    manifest = {
        "source_edition_date": prior.get("edition_date"),
        "topic_count": len(topics),
        "new_today": [x["topic_id"] for x in topics if x["active"] and daily_state(x["public_topic"], edition_date) == "new_today"],
        "updated_today": [x["topic_id"] for x in topics if x["active"] and daily_state(x["public_topic"], edition_date) == "updated_today"],
        "carried_forward": [x["topic_id"] for x in topics if x["active"] and daily_state(x["public_topic"], edition_date) == "carried_forward"],
        "method": "current_watchlist_source_review_with_evidence_qualification",
        "review_complete": True,
        "review_validation": validation,
    }
    return registry, catalog, manifest


def public_watchlist_from_canonical(canonical: dict[str, Any]) -> dict[str, Any]:
    if canonical.get("status") != "locked":
        raise ValueError("canonical Watchlist artifact is not locked")
    data = canonical.get("data") or {}
    edition_date = str(data.get("edition_date") or canonical.get("edition_date") or "")
    items: list[dict[str, Any]] = []
    for bucket in ("new_today", "updated_today", "carried_forward"):
        for item in data.get(bucket) or []:
            if not isinstance(item.get("public_topic"), dict):
                raise ValueError(f"canonical Watchlist item lacks public_topic: {item.get('topic_id')}")
            items.append(item)
    items.sort(key=lambda x: (int(x.get("presentation_order") or 999999), str(x.get("topic_id") or "")))
    public = {
        "schema_version": "1.0.0",
        "edition_date": edition_date,
        "updated_at": data.get("reviewed_at"),
        "baseline_note": data.get("baseline_note"),
        "canonical_watchlist_digest": canonical.get("content_digest"),
        "counts": deepcopy(data.get("counts") or {}),
        "review_policy": deepcopy(data.get("review_policy") or {}),
        "source_checks": deepcopy(data.get("source_checks") or []),
        "topics": [deepcopy(x["public_topic"]) for x in items],
    }
    validate_public_watchlist(public, canonical, edition_date)
    return public


def validate_public_watchlist(public: dict[str, Any], canonical: dict[str, Any], edition_date: str) -> dict[str, int]:
    if public.get("edition_date") != edition_date:
        raise ValueError("reader Watchlist edition_date is stale or mismatched")
    if canonical.get("status") != "locked" or canonical.get("edition_date") != edition_date:
        raise ValueError("canonical Watchlist identity/date is invalid")
    if public.get("canonical_watchlist_digest") != canonical.get("content_digest"):
        raise ValueError("reader Watchlist digest does not match the locked canonical Watchlist")

    expected = canonical.get("data", {}).get("counts") or {}
    actual = {"new_today": 0, "updated_today": 0, "carried_forward": 0}
    policy = public.get("review_policy") or {}
    new_min = int(policy.get("new_topic_min_independent_sources") or 2)
    for topic in public.get("topics") or []:
        if not topic_is_active(topic):
            continue
        state = daily_state(topic, edition_date)
        actual[state] += 1
        if state in {"new_today", "updated_today"}:
            evidence = [e for e in (topic.get("evidence") or []) if _qualifying_evidence(e, edition_date)]
            if not evidence:
                raise ValueError(f"{state} topic lacks qualifying current-date evidence: {topic.get('topic_id')}")
            if state == "new_today":
                independent = {str(e.get("publisher") or "").strip().lower() for e in evidence}
                if len(evidence) < new_min or len(independent) < new_min:
                    raise ValueError(f"new_today topic is below the approved evidence threshold: {topic.get('topic_id')}")
    if actual != {k: int(expected.get(k) or 0) for k in actual}:
        raise ValueError(f"reader Watchlist counts do not reconcile: actual={actual} expected={expected}")
    return actual
