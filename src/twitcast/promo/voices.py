"""Per-show voice profiles for promotional copy."""

SHOW_VOICE: dict[str, dict[str, str]] = {
    "TWiT": {
        "lead": "We just published a new TWiT flagship episode:",
        "section": "Here's what we're unpacking:",
        "close": "If you listen, tell me what you think.",
        "tags": "#TWiT #Podcast #Tech",
    },
    "SN": {
        "lead": "New Security Now! is live:",
        "section": "In this episode:",
        "close": "I'd especially love your take on the security implications.",
        "tags": "#SecurityNow #Cybersecurity #TWiT",
    },
    "MBW": {
        "lead": "New MacBreak Weekly just dropped:",
        "section": "What we cover:",
        "close": "Let me know which segment hit hardest for you.",
        "tags": "#MacBreakWeekly #Apple #TWiT",
    },
    "WW": {
        "lead": "New Windows Weekly is out now:",
        "section": "This one covers:",
        "close": "Curious what stood out to you most.",
        "tags": "#WindowsWeekly #Microsoft #TWiT",
    },
    "IM": {
        "lead": "Fresh Intelligent Machines is now live:",
        "section": "In this conversation:",
        "close": "I'd love your take after you listen.",
        "tags": "#IntelligentMachines #AI #TWiT",
    },
    "TWiS": {
        "lead": "New This Week in Space is live:",
        "section": "Here's what we get into:",
        "close": "If you're following spaceflight, this one's worth your time.",
        "tags": "#ThisWeekInSpace #Space #TWiT",
    },
    "PLUSSHOWS": {
        "lead": "New Club TWiT release just dropped:",
        "section": "Here's what's inside:",
        "close": "Club members, I'd love your take after you listen.",
        "tags": "#ClubTWiT #TWiT #Podcast",
    },
}

DEFAULT_VOICE: dict[str, str] = {
    "lead": "We just published a new episode on TWiT:",
    "section": "Here's what we get into:",
    "close": "I'd love your take after you listen.",
    "tags": "#TWiT #Podcast #TechNews",
}


def get_voice(show_code: str) -> dict[str, str]:
    """Get the voice profile for a show, falling back to default."""
    return SHOW_VOICE.get(show_code, DEFAULT_VOICE)
