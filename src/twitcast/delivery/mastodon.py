"""Mastodon API: post statuses to a Mastodon instance."""

import logging

import requests

from twitcast.config import Config

log = logging.getLogger(__name__)

MAX_STATUS_LENGTH = 500


def post_status(config: Config, content: str) -> bool:
    """Post a status to Mastodon.

    Truncates content to 500 characters if needed.
    Returns True on success, False on failure or missing credentials.
    """
    mc = config.mastodon
    if not mc.access_token or not mc.instance_url:
        log.info("No Mastodon credentials configured, skipping")
        return False

    if len(content) > MAX_STATUS_LENGTH:
        log.warning("Mastodon status truncated from %d to %d chars", len(content), MAX_STATUS_LENGTH)
        content = content[:497] + "..."

    url = f"{mc.instance_url.rstrip('/')}/api/v1/statuses"
    headers = {"Authorization": f"Bearer {mc.access_token}"}
    payload = {
        "status": content,
        "visibility": mc.visibility,
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        status_url = resp.json().get("url", "")
        log.info("Posted to Mastodon: %s", status_url)
        return True
    except requests.RequestException as e:
        log.warning("Mastodon API post failed: %s", e)
        return False
