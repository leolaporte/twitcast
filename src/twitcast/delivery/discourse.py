"""Discourse API: create topics on twit.community."""

import logging

import requests

from twitcast.config import Config

log = logging.getLogger(__name__)

# Discourse subcategory IDs under "TWiT Shows" (parent_category_id=5)
SHOW_CATEGORY_IDS = {
    "This Week In Tech": 13,
    "This Week in Tech": 13,
    "MacBreak Weekly": 14,
    "iOS Today": 15,
    "Security Now": 16,
    "Windows Weekly": 17,
    "Hands-On Tech": 22,
    "Tech News Weekly": 32,
    "This Week in Space": 80,
    "Hands-On Windows": 81,
    "Home Theater Geeks": 84,
    "Untitled Linux Show": 85,
    "Intelligent Machines": 89,
    "Hands-On Apple": 90,
}

# Fallback: parent "TWiT Shows" category
TWIT_SHOWS_CATEGORY_ID = 5


def post_topic(
    config: Config,
    show_code: str,
    episode_number: str | int,
    show_label: str,
    episode_title: str,
    body: str,
    category_id: int | None = None,
) -> dict | None:
    """Create a new Discourse topic.

    Title format: "{show_code} {episode_number}: {episode_title}"
    Category: show-specific subcategory under TWiT Shows, or TWiT Shows parent.
    Tag: "episode"

    Returns the API response dict on success, None on failure.
    """
    dc = config.discourse
    if not dc.api_key or not dc.api_username:
        log.info("No Discourse API credentials configured, skipping")
        return None

    title = f"{show_code} {episode_number}: {episode_title}"

    if category_id is None:
        category_id = SHOW_CATEGORY_IDS.get(show_label, TWIT_SHOWS_CATEGORY_ID)

    payload = {
        "title": title,
        "raw": body,
        "category": category_id,
        "tags": ["episode"],
    }

    headers = {
        "Api-Key": dc.api_key,
        "Api-Username": dc.api_username,
        "Content-Type": "application/json",
    }

    try:
        resp = requests.post(
            f"{dc.base_url}/posts.json",
            headers=headers,
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        topic_id = data.get("topic_id")
        log.info("Discourse topic created: %s/t/%s", dc.base_url, topic_id)
        return data
    except requests.RequestException as e:
        log.warning("Discourse API post failed: %s", e)
        return None
