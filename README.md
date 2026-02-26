# TWiTCast

Podcast tools for the [TWiT](https://twit.tv) network — e-ink dashboard, episode promos, and transcript summaries.

![Dashboard preview](preview.png)

## What it does

**`twitcast dashboard`** — Renders an 800×480 e-ink dashboard showing the three most recent episodes with artwork, Club TWiT member count, and YouTube subscriber stats. Pushes to a Raspberry Pi display and posts to Discord.

**`twitcast promo`** — Watches for new episode transcripts and generates conversational promotional posts using Claude Haiku. Posts to Discord and Discourse. Falls back to a template if the AI is unavailable.

**`twitcast summarize`** — Summarizes the latest episode transcript into key topics, a brief summary, and a notable quote.

**`twitcast shows`** — Lists all active TWiT shows with their IDs and short codes.

## Setup

Requires Python 3.12+.

```bash
python -m venv .venv
.venv/bin/pip install -e .
```

Copy `config.toml.example` to `config.toml` and set credentials via environment variables:

| Variable | Service |
|---|---|
| `TWIT_APP_ID`, `TWIT_APP_KEY` | TWiT API |
| `MEMBERFUL_API_USER_ID`, `MEMBERFUL_API_KEY` | Memberful (member count) |
| `YOUTUBE_API_KEY` | YouTube Data API (subscriber counts) |
| `ANTHROPIC_API_KEY` | Claude Haiku (AI promos & summaries) |
| `DISCORD_WEBHOOK_URL` | Discord delivery |
| `DISCOURSE_API_KEY`, `DISCOURSE_API_USERNAME` | Discourse (twit.community) |

## Usage

```bash
# Render dashboard locally
twitcast dashboard --preview

# Render and deliver to Pi + Discord
twitcast dashboard

# Preview promos without posting
twitcast promo --dry-run

# Post promos (skips already-posted episodes)
twitcast promo

# Summarize the latest episode
twitcast summarize
```

## Automation

Systemd user timers are included in `systemd/`:

| Timer | Schedule | Command |
|---|---|---|
| `twitcast-dashboard.timer` | Daily at 11:00 AM Pacific | `twitcast dashboard` |
| `twitcast-promo.timer` | Every 30 minutes | `twitcast promo` |

Install them:

```bash
ln -sf "$(pwd)"/systemd/twitcast-*.service ~/.config/systemd/user/
ln -sf "$(pwd)"/systemd/twitcast-*.timer ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now twitcast-dashboard.timer twitcast-promo.timer
```

Timers expect credentials in `~/.secrets.env`.

## Architecture

```
src/twitcast/
├── cli.py                  # Click CLI entry point
├── config.py               # TOML + env var config loading
├── shows.py                # Show metadata and slug mappings
├── cache.py                # TTL-based JSON file cache
├── api/
│   ├── twit.py             # TWiT REST API (episodes, shows)
│   ├── memberful.py        # Memberful GraphQL (member count)
│   ├── youtube.py          # YouTube Data API (subscriber counts)
│   └── anthropic_client.py # Claude Haiku (summarize, write promo)
├── transcript/
│   ├── resolver.py         # Finds transcript URLs by probing candidates
│   ├── parser.py           # HTML stripping and bullet extraction
│   └── summarizer.py       # Orchestrates AI summarization
├── promo/
│   ├── builder.py          # Template and AI promo assembly
│   └── voices.py           # Per-show voice/tone profiles
├── dashboard/
│   ├── renderer.py         # PIL-based 800×480 image rendering
│   ├── layout.py           # Layout constants
│   └── fonts.py            # Font loading with fallback
└── delivery/
    ├── discord.py           # Discord webhook (image + text)
    ├── discourse.py         # Discourse topic creation
    └── pi.py                # SCP + SSH to Raspberry Pi
```
