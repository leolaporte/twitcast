"""Haiku wrapper: summarize transcripts and write promotional copy."""

import logging

import anthropic

from twitcast.config import Config

log = logging.getLogger(__name__)

SUMMARIZE_SYSTEM = """You are summarizing a TWiT network podcast episode transcript.
Produce a JSON object with exactly these keys:
1. "summary": 3-5 sentence summary of the episode
2. "topics": array of 3-5 bullet-point topic strings
3. "notable_quote": one notable quote with speaker attribution

Return ONLY valid JSON, no markdown fences."""

MASTODON_SYSTEM = """Condense this announcement to fit within 500 characters (including the URL and hashtags).
Keep it factual and brief. Use 2-3 bullet points max, no emoji. Keep the episode URL and hashtags.
Return ONLY the shortened post, nothing else."""

PROMO_SYSTEM_TEMPLATE = """Write a straightforward episode announcement for {show_name} #{number} - "{title}".
Based on this summary: {summary}

Additional topics covered: {topics}

Format:
- One sentence stating the episode is available
- 3-5 bullet points listing topics covered (plain text, no emoji)
- Episode URL on its own line
- Relevant hashtags on the final line

Keep it under 120 words. Factual and informative — this is an announcement, not a sales pitch.
Episode URL: {episode_url}"""


def _get_client(config: Config) -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.anthropic.api_key)


def summarize_transcript(
    config: Config,
    transcript_text: str,
    show_name: str,
    episode_number: str | int,
    title: str,
) -> str | None:
    """Call Haiku to summarize a transcript. Returns raw response text."""
    if not config.anthropic.api_key:
        log.error("No Anthropic API key configured")
        return None

    client = _get_client(config)
    try:
        message = client.messages.create(
            model=config.anthropic.model,
            max_tokens=1024,
            system=SUMMARIZE_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"Summarize this transcript of {show_name} #{episode_number} - \"{title}\":\n\n{transcript_text}",
            }],
        )
        return message.content[0].text
    except anthropic.APIError as e:
        log.error("Anthropic API summarization failed: %s", e)
        return None


def write_promo(
    config: Config,
    summary: str,
    topics: list[str],
    show_name: str,
    episode_number: str | int,
    title: str,
    episode_url: str,
    voice_profile: dict,
) -> str | None:
    """Call Haiku to write promotional copy. Returns the promo text."""
    if not config.anthropic.api_key:
        log.error("No Anthropic API key configured")
        return None

    voice_str = ". ".join(f"{k}: {v}" for k, v in voice_profile.items())
    topics_str = ", ".join(topics) if topics else "various tech topics"

    system_prompt = PROMO_SYSTEM_TEMPLATE.format(
        show_name=show_name,
        number=episode_number,
        title=title,
        voice_profile=voice_str,
        summary=summary,
        topics=topics_str,
        episode_url=episode_url,
    )

    client = _get_client(config)
    try:
        message = client.messages.create(
            model=config.anthropic.model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": "Write the promotional post now.",
            }],
        )
        return message.content[0].text
    except anthropic.APIError as e:
        log.error("Anthropic API promo generation failed: %s", e)
        return None


def shorten_for_mastodon(config: Config, promo_text: str) -> str | None:
    """Condense a promo post to <=500 characters for Mastodon. Returns shortened text."""
    if not config.anthropic.api_key:
        log.error("No Anthropic API key configured")
        return None

    client = _get_client(config)
    try:
        message = client.messages.create(
            model=config.anthropic.model,
            max_tokens=512,
            system=MASTODON_SYSTEM,
            messages=[{
                "role": "user",
                "content": promo_text,
            }],
        )
        return message.content[0].text
    except anthropic.APIError as e:
        log.error("Anthropic API mastodon shortening failed: %s", e)
        return None
