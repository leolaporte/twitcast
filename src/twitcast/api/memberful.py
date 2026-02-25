"""Memberful GraphQL API: member count with pagination and caching."""

import json
import logging

import requests

from twitcast.cache import read_cache, write_cache
from twitcast.config import CACHE_DIR, Config

MEMBERFUL_CACHE = CACHE_DIR / "memberful.json"

log = logging.getLogger(__name__)


def fetch_memberful_count(config: Config) -> int | None:
    """Fetch active paid member count from Memberful GraphQL API.

    Paginates through all members, counts those with active subscription
    and a credit card on file. Caches result to avoid frequent re-queries.
    """
    refresh_hours = config.display.memberful_refresh_hours
    cached = read_cache(MEMBERFUL_CACHE, refresh_hours)
    if cached is not None:
        log.info("Using cached member count: %d", cached["count"])
        return cached["count"]

    mc = config.memberful
    if not mc.api_key:
        log.warning("No Memberful API key configured")
        return _load_fallback()

    url = f"{mc.api_url}?api_user_id={mc.api_user_id}"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {mc.api_key}",
        "Cache-Control": "no-cache",
    }

    active_count = 0
    has_next = True
    cursor = None
    page = 0

    while has_next:
        page += 1
        after_clause = f', after: "{cursor}"' if cursor else ""
        query = json.dumps({"query":
            "{ members(first: 100" + after_clause
            + ") { pageInfo { endCursor hasNextPage } "
            + "edges { node { creditCard { brand } subscriptions { active } } } } }"
        })
        try:
            resp = requests.post(url, headers=headers, data=query, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            log.error("Memberful API request failed on page %d: %s", page, e)
            return _load_fallback()

        members = data.get("data", {}).get("members", {})
        page_info = members.get("pageInfo", {})
        has_next = page_info.get("hasNextPage", False)
        cursor = page_info.get("endCursor")

        for edge in members.get("edges", []):
            node = edge.get("node", {})
            subs = node.get("subscriptions", [])
            card = node.get("creditCard")
            if subs and subs[0].get("active") and card and card.get("brand"):
                active_count += 1

        log.info("Memberful page %d: running count = %d", page, active_count)

    write_cache(MEMBERFUL_CACHE, {"count": active_count})
    log.info("Memberful total active paid members: %d", active_count)
    return active_count


def _load_fallback() -> int | None:
    """Load last cached member count as fallback."""
    if MEMBERFUL_CACHE.exists():
        try:
            with open(MEMBERFUL_CACHE) as f:
                data = json.load(f)
            log.info("Falling back to cached count: %d", data["count"])
            return data["count"]
        except (json.JSONDecodeError, KeyError):
            pass
    return None
