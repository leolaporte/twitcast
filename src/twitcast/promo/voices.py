"""Per-show voice profiles for promotional copy."""


SHOW_VOICE: dict[str, dict[str, str]] = {
    "TWiT": {
        "lead": "New episode of This Week in Tech:",
        "section": "Topics covered:",
        "tags": "#TWiT #Podcast #Tech",
    },
    "SN": {
        "lead": "New episode of Security Now:",
        "section": "Topics covered:",
        "tags": "#SecurityNow #Cybersecurity #TWiT",
    },
    "MBW": {
        "lead": "New episode of MacBreak Weekly:",
        "section": "Topics covered:",
        "tags": "#MacBreakWeekly #Apple #TWiT",
    },
    "WW": {
        "lead": "New episode of Windows Weekly:",
        "section": "Topics covered:",
        "tags": "#WindowsWeekly #Microsoft #TWiT",
    },
    "IM": {
        "lead": "New episode of Intelligent Machines:",
        "section": "Topics covered:",
        "tags": "#IntelligentMachines #AI #TWiT",
    },
    "TWiS": {
        "lead": "New episode of This Week in Space:",
        "section": "Topics covered:",
        "tags": "#ThisWeekInSpace #Space #TWiT",
    },
    "PLUSSHOWS": {
        "lead": "New Club TWiT episode available:",
        "section": "Topics covered:",
        "tags": "#ClubTWiT #TWiT #Podcast",
    },
}

DEFAULT_VOICE: dict[str, str] = {
    "lead": "New episode from the TWiT network:",
    "section": "Topics covered:",
    "tags": "#TWiT #Podcast #TechNews",
}


def get_voice(show_code: str) -> dict[str, str]:
    """Get the voice profile for a show."""
    return SHOW_VOICE.get(show_code, DEFAULT_VOICE).copy()
