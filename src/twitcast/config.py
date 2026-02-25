"""Configuration loading: TOML file + environment variable overlay."""

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path

import tomllib

PROJECT_DIR = Path(__file__).parent.parent.parent
CONFIG_PATH = PROJECT_DIR / "config.toml"
CACHE_DIR = PROJECT_DIR / "cache"


ENV_MAP = {
    ("twit", "app_id"): "TWIT_APP_ID",
    ("twit", "app_key"): "TWIT_APP_KEY",
    ("memberful", "api_key"): "MEMBERFUL_API_KEY",
    ("memberful", "api_user_id"): "MEMBERFUL_API_USER_ID",
    ("youtube", "api_key"): "YOUTUBE_API_KEY",
    ("anthropic", "api_key"): ("ANTHROPIC_API_KEY", "CLAUDE_API_KEY"),
    ("discord", "webhook_url"): "DISCORD_WEBHOOK_URL",
    ("discourse", "api_key"): "DISCOURSE_API_KEY",
    ("discourse", "api_username"): "DISCOURSE_API_USERNAME",
}


@dataclass(frozen=True)
class TwitConfig:
    app_id: str = ""
    app_key: str = ""


@dataclass(frozen=True)
class MemberfulConfig:
    api_url: str = "https://twit.memberful.com/api/graphql"
    api_key: str = ""
    api_user_id: str = ""


@dataclass(frozen=True)
class YouTubeConfig:
    api_key: str = ""


@dataclass(frozen=True)
class AnthropicConfig:
    api_key: str = ""
    model: str = "claude-haiku-4-5-20251001"


@dataclass(frozen=True)
class PiConfig:
    host: str = ""
    user: str = "pi"
    image_path: str = "/home/pi/dashboard.png"
    display_script: str = "/home/pi/display.py"


@dataclass(frozen=True)
class DiscordConfig:
    webhook_url: str = ""


@dataclass(frozen=True)
class DiscourseConfig:
    base_url: str = "https://twit.community"
    api_key: str = ""
    api_username: str = ""


@dataclass(frozen=True)
class DisplayConfig:
    memberful_refresh_hours: float = 4


@dataclass(frozen=True)
class Config:
    twit: TwitConfig = field(default_factory=TwitConfig)
    memberful: MemberfulConfig = field(default_factory=MemberfulConfig)
    youtube: YouTubeConfig = field(default_factory=YouTubeConfig)
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    pi: PiConfig = field(default_factory=PiConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)
    discourse: DiscourseConfig = field(default_factory=DiscourseConfig)
    display: DisplayConfig = field(default_factory=DisplayConfig)


def load_config(config_path: Path | None = None) -> Config:
    """Load config from TOML file with environment variable overlay."""
    path = config_path or CONFIG_PATH
    if not path.exists():
        print(f"Error: {path} not found.", file=sys.stderr)
        sys.exit(1)

    with open(path, "rb") as f:
        raw = tomllib.load(f)

    # Overlay environment variables
    for (section, key), env_names in ENV_MAP.items():
        if isinstance(env_names, str):
            env_names = (env_names,)
        for env_var in env_names:
            value = os.environ.get(env_var)
            if value:
                raw.setdefault(section, {})[key] = value
                break

    return Config(
        twit=TwitConfig(**{k: v for k, v in raw.get("twit", {}).items() if k in TwitConfig.__dataclass_fields__}),
        memberful=MemberfulConfig(**{k: v for k, v in raw.get("memberful", {}).items() if k in MemberfulConfig.__dataclass_fields__}),
        youtube=YouTubeConfig(**{k: v for k, v in raw.get("youtube", {}).items() if k in YouTubeConfig.__dataclass_fields__}),
        anthropic=AnthropicConfig(**{k: v for k, v in raw.get("anthropic", {}).items() if k in AnthropicConfig.__dataclass_fields__}),
        pi=PiConfig(**{k: v for k, v in raw.get("pi", {}).items() if k in PiConfig.__dataclass_fields__}),
        discord=DiscordConfig(**{k: v for k, v in raw.get("discord", {}).items() if k in DiscordConfig.__dataclass_fields__}),
        discourse=DiscourseConfig(**{k: v for k, v in raw.get("discourse", {}).items() if k in DiscourseConfig.__dataclass_fields__}),
        display=DisplayConfig(**{k: v for k, v in raw.get("display", {}).items() if k in DisplayConfig.__dataclass_fields__}),
    )
