"""Discord webhook: image and text posting."""

import logging
from pathlib import Path

import requests

from twitcast.config import Config

log = logging.getLogger(__name__)


def post_image(config: Config, image_path: Path) -> bool:
    """Post rendered dashboard image to Discord via webhook."""
    webhook_url = config.discord.webhook_url
    if not webhook_url:
        log.info("No Discord webhook_url configured, skipping")
        return False

    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                webhook_url,
                files={"file": ("dashboard.png", f, "image/png")},
                timeout=30,
            )
            resp.raise_for_status()
        log.info("Image posted to Discord webhook")
        return True
    except requests.RequestException as e:
        log.warning("Discord webhook failed: %s", e)
        return False


def post_text(config: Config, content: str) -> bool:
    """Post text content to Discord via webhook."""
    webhook_url = config.discord.webhook_url
    if not webhook_url:
        log.info("No Discord webhook_url configured, skipping")
        return False

    # Discord text message limit is 2000 chars
    if len(content) > 1990:
        content = content[:1987] + "..."

    try:
        resp = requests.post(webhook_url, json={"content": content}, timeout=30)
        resp.raise_for_status()
        log.info("Text posted to Discord webhook")
        return True
    except requests.RequestException as e:
        log.warning("Discord webhook text post failed: %s", e)
        return False
