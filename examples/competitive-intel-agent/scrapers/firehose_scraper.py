"""
Ahrefs Firehose scraper — real-time web mentions via SSE.

Firehose (https://firehose.com) streams pages crawled by Ahrefs' infrastructure
that match Lucene rules you define.  It's free and has far broader coverage than
any single-site scraper.

API overview
------------
- Management key (fhm_...) : create/list/delete taps and rules
- Tap token     (fh_...)   : stream events and manage rules on one tap
- SSE endpoint             : GET https://api.firehose.com/v1/stream
- Buffering                : up to 24 hours (`since=24h` replays the buffer)
- Rule syntax              : Lucene — title:, domain:, url:, recent:, AND/OR/NOT
- Docs                     : https://firehose.com/api-docs

For competitive intelligence we:
  1. Bootstrap: create one tap + one rule per competitor (idempotent)
  2. Daily pull: connect to SSE with `since=24h`, drain buffered events, store them
  3. Live mode (optional): keep connection open to receive events in real-time
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Generator

import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import COMPETITORS
from storage.database import insert_raw_event

log = logging.getLogger(__name__)

FIREHOSE_API_BASE = "https://api.firehose.com/v1"

# ── Per-competitor Lucene rules ───────────────────────────────────────────────
# Each rule uses Ahrefs Firehose's Lucene syntax.
# `recent:24h` restricts to pages published in the last 24 hours.
# We tag each rule so we can route events back to the right competitor.

COMPETITOR_RULES: dict[str, list[dict]] = {
    "duck_creek": [
        {"value": '"Duck Creek Technologies" AND recent:24h', "tag": "duck_creek"},
        {"value": 'title:"Duck Creek" AND recent:24h',       "tag": "duck_creek"},
    ],
    "sapiens": [
        {"value": '"Sapiens International" AND recent:24h',  "tag": "sapiens"},
        {"value": 'title:"Sapiens" AND insurance AND recent:24h', "tag": "sapiens"},
    ],
    "majesco": [
        {"value": '"Majesco" AND insurance AND recent:24h',  "tag": "majesco"},
        {"value": 'title:"Majesco" AND recent:24h',          "tag": "majesco"},
    ],
    "insurity": [
        {"value": '"Insurity" AND recent:24h',               "tag": "insurity"},
        {"value": 'title:"Insurity" AND recent:24h',         "tag": "insurity"},
    ],
    "applied_systems": [
        {"value": '"Applied Systems" AND insurance AND recent:24h', "tag": "applied_systems"},
        {"value": 'title:"Applied Epic" AND recent:24h',            "tag": "applied_systems"},
    ],
    "one_shield": [
        {"value": '"OneShield" AND recent:24h',              "tag": "one_shield"},
    ],
}

# Tag → competitor_id reverse map (built from COMPETITOR_RULES at import time)
TAG_TO_COMPETITOR: dict[str, str] = {
    rule["tag"]: cid
    for cid, rules in COMPETITOR_RULES.items()
    for rule in rules
}


# ── Client helpers ────────────────────────────────────────────────────────────

def _management_headers(mgmt_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {mgmt_key}",
        "Content-Type": "application/json",
    }


def _tap_headers(tap_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {tap_token}",
        "Content-Type": "application/json",
    }


# ── Tap management ─────────────────────────────────────────────────────────────

def create_tap(mgmt_key: str, name: str = "guidewire-ci") -> dict:
    """
    Create a new tap and return the full tap object (including the fh_ token).
    Idempotent: if a tap with this name exists, return it.
    """
    existing = list_taps(mgmt_key)
    for tap in existing:
        if tap.get("name") == name:
            log.info("Tap '%s' already exists (uuid: %s)", name, tap.get("uuid"))
            return tap

    resp = requests.post(
        f"{FIREHOSE_API_BASE}/taps",
        headers=_management_headers(mgmt_key),
        json={"name": name},
        timeout=15,
    )
    resp.raise_for_status()
    tap = resp.json().get("data", {})
    log.info("Created tap '%s' (uuid: %s)", name, tap.get("uuid"))
    return tap


def list_taps(mgmt_key: str) -> list[dict]:
    resp = requests.get(
        f"{FIREHOSE_API_BASE}/taps",
        headers=_management_headers(mgmt_key),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


# ── Rule management ───────────────────────────────────────────────────────────

def list_rules(tap_token: str) -> list[dict]:
    resp = requests.get(
        f"{FIREHOSE_API_BASE}/rules",
        headers=_tap_headers(tap_token),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def create_rule(tap_token: str, value: str, tag: str) -> dict:
    resp = requests.post(
        f"{FIREHOSE_API_BASE}/rules",
        headers=_tap_headers(tap_token),
        json={"value": value, "tag": tag},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


def bootstrap_rules(tap_token: str) -> int:
    """
    Ensure all per-competitor Lucene rules exist on the tap.
    Skips rules that already exist (matched by tag+value).
    Returns the count of newly created rules.
    """
    existing = list_rules(tap_token)
    existing_values = {r.get("value") for r in existing}
    created = 0

    for cid, rules in COMPETITOR_RULES.items():
        for rule in rules:
            if rule["value"] in existing_values:
                log.debug("Rule already exists: %s", rule["value"][:60])
                continue
            create_rule(tap_token, rule["value"], rule["tag"])
            log.info("Created rule [%s]: %s", cid, rule["value"][:80])
            created += 1
            time.sleep(0.3)   # polite delay

    return created


# ── SSE streaming ─────────────────────────────────────────────────────────────

def _parse_sse_events(response: requests.Response) -> Generator[dict, None, None]:
    """
    Parse a raw SSE stream from the Firehose API.
    Yields parsed JSON dicts from `data:` lines.
    """
    event_data_lines: list[str] = []
    for raw_line in response.iter_lines(decode_unicode=True):
        if not raw_line:
            # Blank line = end of one SSE event
            if event_data_lines:
                payload = "\n".join(event_data_lines)
                try:
                    yield json.loads(payload)
                except json.JSONDecodeError:
                    log.warning("Could not parse SSE payload: %s", payload[:120])
                event_data_lines = []
            continue

        if raw_line.startswith("data:"):
            event_data_lines.append(raw_line[5:].lstrip())
        elif raw_line.startswith(":"):
            # SSE comment / heartbeat — ignore
            pass


def stream_events(
    tap_token: str,
    *,
    since: str = "24h",
    limit: int | None = None,
    timeout: int = 60,
) -> Generator[dict, None, None]:
    """
    Open an SSE connection and yield raw Firehose event dicts.

    Parameters
    ----------
    since   : replay buffer window, e.g. "24h", "1h", "7d" (max 24h)
    limit   : close stream after this many matching events (None = drain buffer)
    timeout : requests read timeout in seconds (keep short for batch mode)
    """
    params: dict[str, str | int] = {"since": since}
    if limit is not None:
        params["limit"] = limit

    log.info("Opening Firehose SSE stream (since=%s, limit=%s)", since, limit)

    with requests.get(
        f"{FIREHOSE_API_BASE}/stream",
        headers={
            "Authorization": f"Bearer {tap_token}",
            "Accept": "text/event-stream",
            "Cache-Control": "no-cache",
        },
        params=params,
        stream=True,
        timeout=(10, timeout),
    ) as resp:
        resp.raise_for_status()
        yield from _parse_sse_events(resp)


# ── Daily pull: drain buffer → store events ───────────────────────────────────

def pull_and_store_events(
    tap_token: str,
    *,
    since: str = "24h",
    max_events: int = 5000,
) -> dict[str, int]:
    """
    Drain the Firehose buffer for the past `since` window, storing each
    matching event as a raw_event in the database.

    Returns {competitor_id: events_stored}.
    """
    counts: dict[str, int] = {cid: 0 for cid in COMPETITORS}
    total = 0

    for event in stream_events(tap_token, since=since, limit=max_events):
        # Firehose event shape (based on docs):
        # {
        #   "url": "...",
        #   "title": "...",
        #   "content": "...",  or "description": "..."
        #   "published_at": "...",
        #   "domain": "...",
        #   "tags": ["duck_creek"],
        #   ...
        # }
        tags = event.get("tags") or event.get("matching_rules", [])
        if isinstance(tags, list):
            tag_strs = [
                t.get("tag", t) if isinstance(t, dict) else str(t)
                for t in tags
            ]
        else:
            tag_strs = []

        # Map tags back to competitor IDs
        competitor_ids = {
            TAG_TO_COMPETITOR[tag]
            for tag in tag_strs
            if tag in TAG_TO_COMPETITOR
        }

        if not competitor_ids:
            # Unmapped tag — store under a generic "other" bucket for review
            competitor_ids = {"_unknown"}

        url = event.get("url", "")
        title = event.get("title", url[:120])
        content = event.get("content") or event.get("description") or event.get("text", "")
        published_at = event.get("published_at") or event.get("crawled_at")
        domain = event.get("domain", "")

        for cid in competitor_ids:
            if cid not in counts:
                counts[cid] = 0
            event_id = insert_raw_event(
                competitor_id=cid,
                source_type="firehose",
                url=url,
                title=title[:200],
                content=content,
                published_at=published_at,
                metadata={
                    "domain": domain,
                    "tags": tag_strs,
                    "language": event.get("language"),
                    "word_count": len(content.split()) if content else 0,
                },
            )
            counts[cid] = counts.get(cid, 0) + 1
            total += 1

    log.info("Firehose pull complete: %d total events stored — %s", total, counts)
    return counts


# ── Bootstrap helper (called once on first run) ────────────────────────────────

def bootstrap(mgmt_key: str, tap_name: str = "guidewire-ci") -> str:
    """
    One-time setup: create the tap and install all competitor rules.
    Returns the tap token (fh_...) — store this in your .env as FIREHOSE_TAP_TOKEN.
    """
    tap = create_tap(mgmt_key, tap_name)
    tap_token = tap.get("token") or tap.get("tap_token") or tap.get("fh_token", "")
    if not tap_token:
        raise ValueError(
            "Could not extract tap token from Firehose response. "
            f"Full tap object: {tap}"
        )

    n = bootstrap_rules(tap_token)
    log.info("Bootstrap complete — %d new rules created. Tap token: %s…", n, tap_token[:12])
    return tap_token
