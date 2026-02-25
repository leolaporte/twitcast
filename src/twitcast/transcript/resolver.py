"""Transcript URL slug candidates and probing."""

import html
import logging
import re

import requests

TRANSCRIPT_BASE = "https://twit.tv/posts/transcripts"

log = logging.getLogger(__name__)


def slugify(text: str) -> str:
    """Convert text to URL slug."""
    text = html.unescape(text or "").lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-")


def transcript_slug_candidates(show_slug: str, show_label: str, episode_number: int | str | None) -> list[str]:
    """Generate candidate transcript URL slugs."""
    candidates = []
    if not episode_number:
        return candidates

    episode_number = str(episode_number)
    stop_words = {"this", "in", "the", "a", "an", "of", "to"}

    def add(prefix):
        if prefix:
            candidates.append(f"{prefix}-{episode_number}-transcript")

    add(show_slug)
    if show_slug.startswith("this-"):
        add(show_slug.removeprefix("this-"))

    compact_slug = "-".join(
        part for part in show_slug.split("-") if part and part not in stop_words
    )
    add(compact_slug)

    label_slug = slugify(show_label)
    add(label_slug)
    compact_label_slug = "-".join(
        part for part in label_slug.split("-") if part and part not in stop_words
    )
    add(compact_label_slug)

    # Deduplicate preserving order
    seen = set()
    ordered = []
    for cand in candidates:
        if cand not in seen:
            ordered.append(cand)
            seen.add(cand)
    return ordered


def fetch_transcript_html(url: str) -> str | None:
    """Fetch a transcript URL and validate it contains actual transcript content."""
    try:
        resp = requests.get(url, timeout=30)
    except requests.RequestException as e:
        log.warning("Transcript fetch failed for %s: %s", url, e)
        return None
    if resp.status_code != 200:
        return None
    body = resp.text
    if "Transcript" not in body:
        return None
    if not re.search(r"\[\d{2}:\d{2}:\d{2}\]:", body):
        return None
    return body


def resolve_transcript_url(
    show_slug: str, show_label: str, episode_number: int | str | None
) -> tuple[str | None, str | None, list[str]]:
    """Probe candidate URLs until a valid transcript is found.

    Returns (transcript_url, transcript_html, attempted_urls).
    """
    attempted = []
    for slug in transcript_slug_candidates(show_slug, show_label, episode_number):
        url = f"{TRANSCRIPT_BASE}/{slug}"
        attempted.append(url)
        html_doc = fetch_transcript_html(url)
        if html_doc:
            return url, html_doc, attempted
    return None, None, attempted
