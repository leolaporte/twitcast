"""Promo copy assembly: template and AI modes."""

import logging

from twitcast.api.twit import TWIT_WEB_URL
from twitcast.config import Config
from twitcast.promo.voices import get_voice
from twitcast.transcript.parser import extract_list_items, strip_html
from twitcast.transcript.summarizer import generate_ai_promo, summarize_episode

log = logging.getLogger(__name__)


def build_template_promo(episode: dict) -> str:
    """Build promotional copy using the template-based approach."""
    title = episode.get("label", "New Episode")
    clean_path = episode.get("cleanPath") or ""
    show = (episode.get("_embedded", {}).get("shows") or [{}])[0]
    show_name = show.get("label", "TWiT Show")
    episode_number = episode.get("episodeNumber", "?")
    airing = episode.get("airingDate", "")
    episode_url = f"{TWIT_WEB_URL}{clean_path}"

    notes_items = extract_list_items(episode.get("showNotes", ""))

    bullets = []
    for item in notes_items:
        if len(bullets) >= 3:
            break
        if item and item not in bullets:
            bullets.append(item)
    while len(bullets) < 3:
        fallback = (
            episode.get("teaser")
            or episode.get("metatag_description")
            or "Sharp analysis and standout insights from the TWiT network."
        )
        fallback = strip_html(fallback)
        if fallback and fallback not in bullets:
            bullets.append(fallback)
        else:
            break
    bullets = [b.rstrip(".") + "." for b in bullets[:3]]

    show_code = show.get("shortCode", "").strip()
    episode_ref = f"{show_name} #{episode_number}" if episode_number else show_name
    if show_code:
        episode_ref = f"{episode_ref} ({show_code})"

    voice = get_voice(show_code)

    lines = [
        f"{voice['lead']} {episode_ref} — \"{title}\"",
        "",
        voice["section"],
        *[f"- {b}" for b in bullets],
        "",
        f"Listen/watch: {episode_url}",
        f"Published: {airing}",
        "",
        voice["tags"],
    ]
    return "\n".join(lines)


def build_ai_promo(config: Config, episode: dict) -> str | None:
    """Build promotional copy using Haiku AI from show notes.

    Returns AI-generated promo text, or None on failure (caller should fall back to template).
    """
    show = (episode.get("_embedded", {}).get("shows") or [{}])[0]
    show_name = show.get("label", "TWiT Show")
    show_code = show.get("shortCode", "").strip()
    episode_number = episode.get("episodeNumber", "?")
    title = episode.get("label", "New Episode")
    clean_path = episode.get("cleanPath") or ""
    episode_url = f"{TWIT_WEB_URL}{clean_path}"

    source_html = episode.get("showNotes", "")
    if not source_html:
        log.warning("No show notes available for AI promo")
        return None

    # Step 1: Summarize
    summary = summarize_episode(config, source_html, show_name, episode_number, title)
    if summary is None:
        log.warning("AI summarization failed, falling back to template")
        return None

    # Step 2: Generate promo
    voice = get_voice(show_code)
    promo = generate_ai_promo(
        config, summary, show_name, episode_number, title, episode_url, voice,
    )
    if promo is None:
        log.warning("AI promo generation failed, falling back to template")
        return None

    return promo
