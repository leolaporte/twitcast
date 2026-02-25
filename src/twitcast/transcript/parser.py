"""HTML stripping and transcript highlight extraction."""

import html
import re


def strip_html(text: str) -> str:
    """Strip HTML tags and normalize whitespace."""
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text or "", flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\\s*/?>", "\n", text or "", flags=re.IGNORECASE)
    text = re.sub(r"</p\\s*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"[ \t]+", " ", text).strip()


def extract_list_items(notes_html: str) -> list[str]:
    """Extract <li> items from HTML show notes."""
    items = re.findall(r"<li>(.*?)</li>", notes_html or "", flags=re.IGNORECASE | re.DOTALL)
    cleaned = []
    for item in items:
        txt = strip_html(item)
        if txt:
            cleaned.append(txt)
    return cleaned


def extract_transcript_highlight(transcript_html: str) -> str | None:
    """Extract a usable highlight quote from transcript HTML."""
    text = strip_html(transcript_html)
    # Trim leading page chrome; transcripts include timestamped speaker lines.
    ts_match = re.search(r"\[\d{2}:\d{2}:\d{2}\]:", text)
    if ts_match:
        text = text[ts_match.start():]

    # Prefer the "Coming up on..." line if present.
    m = re.search(
        r"Coming up on .*?,\s*(.*?)\s*(?:So tune in|Recorded on|This is)",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if m:
        sentence = re.sub(r"\s+", " ", m.group(1)).strip(" .")
        if _is_good_highlight(sentence):
            return sentence

    return None


def extract_transcript_bullets(transcript_html: str, max_items: int = 2) -> list[str]:
    """Extract bullet-worthy highlights from a transcript."""
    highlight = extract_transcript_highlight(transcript_html)
    if highlight:
        return [highlight][:max_items]
    return []


def _is_good_highlight(text: str) -> bool:
    """Check whether a highlight excerpt is usable."""
    if not text:
        return False
    cleaned = re.sub(r"\s+", " ", text).strip()
    if len(cleaned) < 80:
        return False
    if len(cleaned.split()) < 12:
        return False
    bad_fragments = [
        "Primary Navigation",
        "Transcript",
        "our leader, Mr.",
        "More….",
    ]
    if any(fragment in cleaned for fragment in bad_fragments):
        return False
    if cleaned.endswith("Mr.") or cleaned.endswith("Ms.") or cleaned.endswith("Dr."):
        return False
    return True
