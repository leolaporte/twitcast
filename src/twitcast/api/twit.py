"""TWiT REST API client: episodes and shows."""

import logging

import requests

from twitcast.config import Config
from twitcast.shows import extract_show_code

TWIT_API_URL = "https://twit.tv/api/v1.0"
TWIT_WEB_URL = "https://twit.tv"

log = logging.getLogger(__name__)


def _headers(config: Config) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "app-id": config.twit.app_id,
        "app-key": config.twit.app_key,
    }


def fetch_episodes(config: Config, count: int = 3) -> list[dict] | None:
    """Fetch most recent episodes from TWiT API.

    Returns list of episode dicts with keys: show_code, show_name,
    airing_date, image_url, episode_id.
    """
    try:
        resp = requests.get(
            f"{TWIT_API_URL}/episodes",
            headers=_headers(config),
            params={"sort": "-airingDate", "range": count},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.error("TWiT API request failed: %s", e)
        return None

    episodes = []
    for item in data.get("episodes", []):
        hero = item.get("heroImage") or {}
        derivatives = hero.get("derivatives") or {}
        image_url = (
            derivatives.get("twit_thumb_720x405")
            or derivatives.get("thumbnail")
            or hero.get("url")
        )
        show_code = extract_show_code(item.get("cleanPath", ""))
        episodes.append({
            "show_code": show_code,
            "show_name": item.get("label", "Unknown"),
            "airing_date": item.get("airingDate"),
            "image_url": image_url,
            "episode_id": item.get("id"),
        })
    return episodes


def fetch_latest_episode(config: Config) -> dict | None:
    """Fetch the single latest episode with full embedded show data."""
    episodes = fetch_recent_episodes(config, count=1)
    return episodes[0] if episodes else None


def fetch_recent_episodes(config: Config, count: int = 10) -> list[dict]:
    """Fetch the N most recent episodes with full embedded show data."""
    try:
        resp = requests.get(
            f"{TWIT_API_URL}/episodes",
            headers=_headers(config),
            params={"sort": "-airingDate", "range": count},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.error("TWiT API request failed: %s", e)
        return []
    return data.get("episodes", [])


def fetch_shows(config: Config) -> list[dict] | None:
    """Fetch all active shows from TWiT API."""
    try:
        resp = requests.get(
            f"{TWIT_API_URL}/shows",
            headers=_headers(config),
            params={"filter[active]": 1},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        log.error("TWiT API shows request failed: %s", e)
        return None

    shows = []
    for item in data.get("shows", []):
        shows.append({
            "id": item.get("id"),
            "label": item.get("label", ""),
            "short_code": item.get("shortCode", ""),
            "slug": (item.get("cleanPath") or "").strip("/").split("/")[-1],
            "clean_path": item.get("cleanPath", ""),
        })
    return shows
