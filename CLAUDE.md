# TWiTCast

Podcast tools for the TWiT network — e-ink dashboard, episode promos, transcript summaries.

## Project Structure

- Python 3.12+, Click CLI, entry point: `src/twitcast/cli.py`
- Config: `config.toml` (TOML + env var overlay via `src/twitcast/config.py`)
- Secrets in env vars loaded from `~/.secrets.env` by systemd
- Venv at `.venv/` — run via `.venv/bin/twitcast` or `.venv/bin/python`
- GitHub: `leolaporte/twitcast` (private, SSH remote)

## Commands

- `twitcast dashboard` — 800x480 e-ink image → Pi + Discord
- `twitcast promo` — AI/template promos → Discord + Discourse + Mastodon
- `twitcast summarize` — transcript summary via Claude Haiku
- `twitcast shows` — list active TWiT shows

## Delivery Targets

| Target | All Shows | Leo's Shows Only |
|--------|-----------|------------------|
| Discord | Yes | — |
| Discourse (twit.community) | Yes | — |
| Mastodon (twit.social) | — | TWiT, MBW, WW, SN, IM |

## Systemd Timers

- `twitcast-dashboard.timer` — daily at 11:00 AM Pacific
- `twitcast-promo.timer` — every 30 minutes

Units symlinked from `systemd/` into `~/.config/systemd/user/`.

## AI Promo Style

- Casual, conversational tone (not salesy/LinkedIn-style)
- 3-5 emoji bullet points (not long paragraphs)
- Under 150 words
- Per-show voice profiles in `src/twitcast/promo/voices.py`

## Key Conventions

- Frozen dataclasses for config (immutable)
- Lazy imports inside Click commands to keep CLI startup fast
- State tracking in `cache/transcript-promo-state.json` (posted episode IDs)
- TTL-based JSON file caching for expensive API calls (Memberful, YouTube)
- AI falls back to template mode on failure
