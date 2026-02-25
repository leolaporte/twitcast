"""Show metadata: codes, slugs, IDs, YouTube channels."""

# Show slug → short code mapping (from TWiT API /shows endpoint)
SHOW_CODES: dict[str, str] = {
    "this-week-in-tech": "TWiT",
    "security-now": "SN",
    "macbreak-weekly": "MBW",
    "windows-weekly": "WW",
    "intelligent-machines": "IM",
    "tech-news-weekly": "TNW",
    "hands-on-tech": "HOT",
    "ios-today": "iOS",
    "this-week-in-space": "TWiS",
    "home-theater-geeks": "HTG",
    "hands-on-apple": "HOA",
    "hands-on-windows": "HOW",
    "untitled-linux-show": "ULS",
    "ai-inside": "AI",
    "twit-plus": "PLUS",
    "twit-plus-club-shows": "PLUSSHOWS",
    "twit-plus-news": "PLUSNEWS",
    "total-leo": "Total Leo",
    "total-mikah": "MIKAH",
    "ask-the-tech-guys": "ATTG",
    "hands-on-android": "H.O.A.",
    "hands-on-photography": "HOP",
}

# YouTube channels: (label, channel_id) — ordered by subscriber count, high to low
YOUTUBE_CHANNELS: list[tuple[str, str]] = [
    ("TWiT", "UCwY9B5_8QDGP8niZhBtTh8w"),
    ("SN", "UCNbqa_9xihC8yaV2o6dlsUg"),
    ("TWiT Show", "UCagoIYmo_gO1iVaCeeSikEg"),
    ("HOT", "UCY96oB1A0TiENISMIy_E2gg"),
    ("MBW", "UC7DLT1zdSVGvnW11y4kqDng"),
    ("WW", "UC1WHdBv9P5tYEGfy-btvYfA"),
    ("iOS", "UCnVDIyVmcIVxb34i0LiD-3w"),
    ("TWiS", "UCQp83PyFvuolpx529fhih_Q"),
]


def extract_show_code(clean_path: str) -> str:
    """Extract show short code from cleanPath like '/shows/this-week-in-tech/episodes/1071'.

    Falls back to uppercased slug initials if show not found in mapping.
    """
    parts = clean_path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "shows":
        slug = parts[1]
        return SHOW_CODES.get(slug, slug.upper()[:6])
    return "???"


def show_slug_from_path(clean_path: str) -> str:
    """Extract the show slug from a cleanPath."""
    parts = clean_path.strip("/").split("/")
    if len(parts) >= 2 and parts[0] == "shows":
        return parts[1]
    return ""
