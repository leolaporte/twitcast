"""YouTube Data API: subscriber counts with caching."""

import json
import logging

import requests

from twitcast.cache import read_cache, write_cache
from twitcast.config import CACHE_DIR, Config
from twitcast.shows import YOUTUBE_CHANNELS

YOUTUBE_CACHE = CACHE_DIR / "youtube.json"

log = logging.getLogger(__name__)


def fetch_youtube_subs(config: Config) -> list[tuple[str, str]] | None:
    """Fetch YouTube subscriber counts for all configured channels.

    Returns list of (label, subscriber_count_str) tuples.
    """
    refresh_hours = config.display.memberful_refresh_hours
    cached = read_cache(YOUTUBE_CACHE, refresh_hours)
    if cached is not None:
        log.info("Using cached YouTube subs")
        return cached["subs"]

    api_key = config.youtube.api_key
    if not api_key:
        log.warning("No YouTube API key configured")
        return _load_fallback()

    channel_ids = ",".join(cid for _, cid in YOUTUBE_CHANNELS)
    try:
        resp = requests.get(
            "https://www.googleapis.com/youtube/v3/channels",
            params={"part": "statistics", "id": channel_ids, "key": api_key},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.error("YouTube API request failed: %s", e)
        return _load_fallback()

    stats_by_id = {}
    for item in data.get("items", []):
        count = int(item["statistics"].get("subscriberCount", 0))
        stats_by_id[item["id"]] = count

    subs = []
    for label, cid in YOUTUBE_CHANNELS:
        count = stats_by_id.get(cid, 0)
        subs.append((label, _format_sub_count(count)))

    write_cache(YOUTUBE_CACHE, {"subs": subs})
    log.info("YouTube subs fetched: %s", subs)
    return subs


def _format_sub_count(count: int) -> str:
    """Format subscriber count like '22.8K' or '280K'."""
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 100_000:
        return f"{count // 1000}K"
    elif count >= 1_000:
        return f"{count / 1000:.1f}K"
    return str(count)


def _load_fallback() -> list[tuple[str, str]] | None:
    """Load last cached YouTube subs as fallback."""
    if YOUTUBE_CACHE.exists():
        try:
            with open(YOUTUBE_CACHE) as f:
                cached = json.load(f)
            return cached["subs"]
        except (json.JSONDecodeError, KeyError):
            pass
    return None
