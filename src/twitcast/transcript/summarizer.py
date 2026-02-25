"""Orchestrates Haiku transcript summarization."""

import json
import logging

from twitcast.api.anthropic_client import summarize_transcript, write_promo
from twitcast.config import Config
from twitcast.transcript.parser import strip_html

log = logging.getLogger(__name__)


def summarize_episode(
    config: Config,
    transcript_html: str,
    show_name: str,
    episode_number: str | int,
    title: str,
) -> dict | None:
    """Summarize a transcript using Haiku.

    Returns dict with keys: summary, topics, notable_quote.
    Returns None on failure.
    """
    text = strip_html(transcript_html)
    # Truncate to ~30K chars to stay within Haiku context
    if len(text) > 30_000:
        text = text[:30_000]

    result = summarize_transcript(config, text, show_name, episode_number, title)
    if result is None:
        return None

    # Parse structured response (strip markdown fences if present)
    try:
        text = result if isinstance(result, str) else str(result)
        text = text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1] if "\n" in text else text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()
        parsed = json.loads(text) if isinstance(result, str) else result
        return {
            "summary": parsed.get("summary", ""),
            "topics": parsed.get("topics", []),
            "notable_quote": parsed.get("notable_quote", ""),
        }
    except (json.JSONDecodeError, AttributeError):
        # If not valid JSON, treat entire response as summary
        return {
            "summary": str(result),
            "topics": [],
            "notable_quote": "",
        }


def generate_ai_promo(
    config: Config,
    summary: dict,
    show_name: str,
    episode_number: str | int,
    title: str,
    episode_url: str,
    voice_profile: dict,
) -> str | None:
    """Generate promotional copy using Haiku.

    Returns the promo text or None on failure.
    """
    return write_promo(
        config,
        summary=summary["summary"],
        topics=summary.get("topics", []),
        show_name=show_name,
        episode_number=episode_number,
        title=title,
        episode_url=episode_url,
        voice_profile=voice_profile,
    )
