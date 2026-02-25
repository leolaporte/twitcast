"""Click CLI: dashboard, promo, summarize, shows."""

import json
import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import click

from twitcast.config import CACHE_DIR, load_config

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

STATE_PATH = CACHE_DIR / "transcript-promo-state.json"
MAX_EPISODE_AGE_DAYS = 14


def _load_state() -> dict:
    if not STATE_PATH.exists():
        return {}
    try:
        with open(STATE_PATH) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_state(state: dict) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def _parse_airing_date(date_str: str | None) -> datetime | None:
    """Parse an ISO 8601 airing date string to a timezone-aware datetime."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str)
    except (ValueError, TypeError):
        return None


@click.group()
def main():
    """TWiT network podcast tools."""
    pass


@main.command()
@click.option("--preview", is_flag=True, help="Save to preview.png, skip delivery")
@click.option("--no-discord", is_flag=True, help="Skip Discord posting")
@click.option("--no-pi", is_flag=True, help="Skip Pi push")
def dashboard(preview, no_discord, no_pi):
    """Render and deliver the e-ink dashboard."""
    from twitcast.api.memberful import fetch_memberful_count
    from twitcast.api.twit import fetch_episodes
    from twitcast.api.youtube import fetch_youtube_subs
    from twitcast.dashboard.renderer import render_dashboard
    from twitcast.delivery.discord import post_image
    from twitcast.delivery.pi import push_to_pi

    config = load_config()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    episodes = fetch_episodes(config)
    if episodes:
        for ep in episodes:
            log.info("  %s: %s (%s)", ep["show_code"], ep["show_name"], ep["airing_date"])
    else:
        log.warning("Failed to fetch episodes")

    member_count = fetch_memberful_count(config)
    log.info("Club TWiT paid members: %s", member_count)

    youtube_subs = fetch_youtube_subs(config)
    if youtube_subs:
        log.info("YouTube subs: %s", youtube_subs)

    img = render_dashboard(episodes or [], member_count, youtube_subs)

    project_dir = Path(__file__).parent.parent.parent
    preview_path = project_dir / "preview.png"
    img.save(preview_path)
    log.info("Image saved to %s", preview_path)

    if preview:
        log.info("Preview mode — skipping delivery")
        return

    if not no_pi:
        push_to_pi(config, preview_path)
    if not no_discord:
        post_image(config, preview_path)


@main.command()
@click.option("--dry-run", is_flag=True, help="Print promo without posting or updating state")
@click.option("--force", is_flag=True, help="Ignore state, post for all recent episodes with transcripts")
@click.option("--no-ai", is_flag=True, help="Use template mode instead of Haiku AI")
@click.option("--no-discourse", is_flag=True, help="Skip Discourse posting")
def promo(dry_run, force, no_ai, no_discourse):
    """Generate and post transcript promos for recent episodes."""
    from twitcast.api.twit import fetch_recent_episodes
    from twitcast.delivery.discord import post_text
    from twitcast.delivery.discourse import post_topic
    from twitcast.promo.builder import build_ai_promo, build_template_promo
    from twitcast.shows import extract_show_code
    from twitcast.transcript.resolver import resolve_transcript_url

    config = load_config()
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    state = _load_state()

    # Load posted IDs, migrating from old single-ID format if needed
    posted_ids = set(state.get("posted_episode_ids", []))
    old_id = state.get("last_posted_episode_id")
    if old_id:
        posted_ids = posted_ids | {old_id}

    episodes = fetch_recent_episodes(config, count=10)
    if not episodes:
        log.warning("No episodes returned from API")
        return

    cutoff = datetime.now(timezone.utc) - timedelta(days=MAX_EPISODE_AGE_DAYS)
    posted_count = 0

    for episode in episodes:
        episode_id = str(episode.get("id"))

        if not force and episode_id in posted_ids:
            continue

        airing_date = _parse_airing_date(episode.get("airingDate"))
        if airing_date and airing_date < cutoff:
            continue

        show = (episode.get("_embedded", {}).get("shows") or [{}])[0]
        show_slug = (show.get("cleanPath") or "").strip("/").split("/")[-1]
        show_label = show.get("label", "")
        show_code = show.get("shortCode", "").strip()
        if not show_code:
            show_code = extract_show_code(episode.get("cleanPath", ""))
        episode_number = episode.get("episodeNumber")

        transcript_url, transcript_html, attempted_urls = resolve_transcript_url(
            show_slug, show_label, episode_number
        )
        if not transcript_url:
            log.info(
                "No transcript yet for %s #%s (episode %s), will retry later",
                show_label, episode_number, episode_id,
            )
            continue

        # Generate promo copy
        promo_text = None
        if not no_ai:
            promo_text = build_ai_promo(config, episode, transcript_url, transcript_html)
        if promo_text is None:
            promo_text = build_template_promo(episode, transcript_url, transcript_html)

        if dry_run:
            click.echo(f"--- {show_label} #{episode_number} (episode {episode_id}) ---")
            click.echo(promo_text)
            click.echo()
            continue

        post_text(config, promo_text)

        if not no_discourse:
            post_topic(
                config,
                show_code=show_code,
                episode_number=episode_number or "?",
                show_label=show_label,
                body=promo_text,
            )

        log.info("Posted promo for %s #%s (episode %s)", show_label, episode_number, episode_id)
        posted_ids = posted_ids | {episode_id}
        posted_count += 1

    if not dry_run:
        _save_state({
            "posted_episode_ids": sorted(posted_ids),
            "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        })

    if posted_count == 0:
        log.info("No new episodes ready for promo")


@main.command()
@click.option("--show", "show_code", help="Show short code to summarize")
@click.option("--episode-id", "episode_id", help="Specific episode ID")
def summarize(show_code, episode_id):
    """Summarize the latest episode transcript using Haiku."""
    from twitcast.api.twit import fetch_latest_episode
    from twitcast.transcript.resolver import resolve_transcript_url
    from twitcast.transcript.summarizer import summarize_episode

    config = load_config()

    episode = fetch_latest_episode(config)
    if not episode:
        log.error("No episodes returned from API")
        sys.exit(1)

    show = (episode.get("_embedded", {}).get("shows") or [{}])[0]
    show_slug = (show.get("cleanPath") or "").strip("/").split("/")[-1]
    show_label = show.get("label", "")
    episode_number = episode.get("episodeNumber")
    title = episode.get("label", "Unknown")

    transcript_url, transcript_html, attempted = resolve_transcript_url(
        show_slug, show_label, episode_number
    )
    if not transcript_html:
        log.error("No transcript found. Tried: %s", ", ".join(attempted))
        sys.exit(1)

    click.echo(f"Summarizing: {show_label} #{episode_number} - {title}")
    click.echo(f"Transcript: {transcript_url}\n")

    result = summarize_episode(config, transcript_html, show_label, episode_number, title)
    if result is None:
        log.error("Summarization failed")
        sys.exit(1)

    click.echo(f"Summary:\n{result['summary']}\n")
    if result["topics"]:
        click.echo("Topics:")
        for topic in result["topics"]:
            click.echo(f"  - {topic}")
        click.echo()
    if result["notable_quote"]:
        click.echo(f"Notable quote: {result['notable_quote']}")


@main.command()
def shows():
    """List all active TWiT shows."""
    from twitcast.api.twit import fetch_shows

    config = load_config()
    show_list = fetch_shows(config)

    if not show_list:
        log.error("Failed to fetch shows")
        sys.exit(1)

    click.echo(f"{'ID':>6}  {'Code':<12}  {'Label'}")
    click.echo("-" * 60)
    for s in show_list:
        click.echo(f"{s['id']:>6}  {s['short_code']:<12}  {s['label']}")
