"""PIL 800x480 dashboard rendering."""

import logging
from datetime import datetime
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from twitcast.config import CACHE_DIR
from twitcast.dashboard.fonts import load_fonts
from twitcast.dashboard.layout import ART_WIDTH, HEIGHT, NUM_TILES, WIDTH

ART_CACHE_DIR = CACHE_DIR / "art"

log = logging.getLogger(__name__)


def download_art(episode: dict) -> Image.Image | None:
    """Download and cache album art for an episode."""
    if not episode.get("image_url"):
        return None

    ART_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = ART_CACHE_DIR / f"{episode['episode_id']}.png"
    if cache_path.exists():
        return Image.open(cache_path)

    try:
        resp = requests.get(episode["image_url"], timeout=15)
        resp.raise_for_status()
        img = Image.open(BytesIO(resp.content)).convert("RGB")
        img.thumbnail((ART_WIDTH, ART_WIDTH), Image.LANCZOS)
        img.save(cache_path, "PNG")
        return img
    except Exception as e:
        log.error("Failed to download art for %s: %s", episode["show_code"], e)
        return None


def format_airing_date(date_str: str | None) -> str:
    """Format an ISO date string to compact 'M/DD H:MMa' format."""
    if not date_str:
        return "\u2014"
    try:
        dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        dt = dt.astimezone()
        hour = dt.hour
        ampm = "a" if hour < 12 else "p"
        hour = hour % 12 or 12
        return f"{dt.month}/{dt.day} {hour}:{dt.minute:02d}{ampm}"
    except (ValueError, TypeError):
        return "\u2014"


def render_dashboard(
    episodes: list[dict],
    member_count: int | None,
    youtube_subs: list[tuple[str, str]] | None = None,
) -> Image.Image:
    """Render the dashboard as an 800x480 PIL Image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)
    font_header, font_code, font_label, font_title, font_date = load_fonts()

    # --- Header bar ---
    header_h = 60
    draw.rectangle([(0, 0), (WIDTH, header_h)], fill=(47, 110, 145))
    count_str = f"{member_count:,}" if member_count is not None else "\u2014"
    header_text = f"CLUB TWiT PAID MEMBERS: {count_str}"
    bbox = draw.textbbox((0, 0), header_text, font=font_header)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    draw.text(
        ((WIDTH - text_w) // 2, (header_h - text_h) // 2),
        header_text,
        fill=(255, 255, 255),
        font=font_header,
    )

    # --- YouTube footer (calculate height first) ---
    footer_h = 0
    footer_lines = []
    if youtube_subs:
        mid = (len(youtube_subs) + 1) // 2
        footer_lines = [youtube_subs[:mid], youtube_subs[mid:]]
        banner_h = 28
        line_h = 24
        footer_h = banner_h + len(footer_lines) * line_h + 10

    # --- Episode tiles ---
    if not episodes and member_count is None:
        _draw_centered(draw, "No data yet \u2014 check network & config", font_label, (180, 180, 180))
        return img

    if not episodes:
        _draw_centered(draw, "No episode data available", font_label, (180, 180, 180))
        return img

    tile_w = ART_WIDTH
    gutter = (WIDTH - tile_w * NUM_TILES) // (NUM_TILES + 1)

    art_images = [download_art(ep) for ep in episodes[:NUM_TILES]]
    max_art_h = max((a.size[1] if a else 0) for a in art_images) or 140

    just_posted_h = 28
    title_line_h = 16
    tile_block_h = just_posted_h + 8 + max_art_h + 6 + title_line_h * 2 + 4 + 26 + 6 + 20
    available_h = HEIGHT - header_h - footer_h
    block_y = header_h + (available_h - tile_block_h) // 2

    # --- "Just Posted" bar ---
    draw.rectangle([(0, block_y), (WIDTH, block_y + just_posted_h)], fill=(255, 255, 255))
    jp_text = "Just Posted"
    bbox = draw.textbbox((0, 0), jp_text, font=font_label)
    jp_w = bbox[2] - bbox[0]
    jp_h = bbox[3] - bbox[1]
    draw.text(
        ((WIDTH - jp_w) // 2, block_y + (just_posted_h - jp_h) // 2),
        jp_text,
        fill=(0, 0, 0),
        font=font_label,
    )

    art_y = block_y + just_posted_h + 8

    for i, ep in enumerate(episodes[:NUM_TILES]):
        tile_x = gutter + i * (tile_w + gutter)
        art = art_images[i]

        if art:
            art_x = tile_x + (tile_w - art.size[0]) // 2
            art_y_offset = art_y + (max_art_h - art.size[1])
            img.paste(art, (art_x, art_y_offset))
        else:
            draw.rectangle(
                [(tile_x, art_y), (tile_x + tile_w, art_y + max_art_h)],
                fill=(60, 60, 60),
            )

        # Episode title in quotes (up to 2 lines)
        title_y = art_y + max_art_h + 6
        raw_title = ep["show_name"]
        title_text = f'"{raw_title}"'
        bbox = draw.textbbox((0, 0), title_text, font=font_title)
        tw = bbox[2] - bbox[0]
        if tw <= tile_w:
            draw.text(
                (tile_x + (tile_w - tw) // 2, title_y),
                title_text,
                fill=(255, 255, 255),
                font=font_title,
            )
        else:
            words = raw_title.split()
            best_split = len(words) // 2 or 1
            line1 = " ".join(words[:best_split])
            line2 = " ".join(words[best_split:])
            for line_idx, line in enumerate([f'"{line1}', f'{line2}"']):
                bbox = draw.textbbox((0, 0), line, font=font_title)
                lw = bbox[2] - bbox[0]
                while lw > tile_w and len(line) > 4:
                    line = line[:-2] + "\u2026"
                    bbox = draw.textbbox((0, 0), line, font=font_title)
                    lw = bbox[2] - bbox[0]
                draw.text(
                    (tile_x + (tile_w - lw) // 2, title_y + line_idx * title_line_h),
                    line,
                    fill=(255, 255, 255),
                    font=font_title,
                )

        # Show code
        label_y = title_y + title_line_h * 2 + 4
        code = ep["show_code"].upper()
        bbox = draw.textbbox((0, 0), code, font=font_code)
        cw = bbox[2] - bbox[0]
        draw.text(
            (tile_x + (tile_w - cw) // 2, label_y),
            code,
            fill=(255, 255, 255),
            font=font_code,
        )

        # Airing date
        date_y = label_y + 26 + 6
        date_str = format_airing_date(ep.get("airing_date"))
        bbox = draw.textbbox((0, 0), date_str, font=font_date)
        dw = bbox[2] - bbox[0]
        draw.text(
            (tile_x + (tile_w - dw) // 2, date_y),
            date_str,
            fill=(200, 200, 200),
            font=font_date,
        )

    # --- YouTube subscriber footer ---
    if youtube_subs and footer_h:
        banner_h = 28
        line_h = 24
        y = HEIGHT - footer_h

        draw.rectangle([(0, y), (WIDTH, y + banner_h)], fill=(180, 30, 30))
        banner_text = "YouTube Subscriber Counts"
        bbox = draw.textbbox((0, 0), banner_text, font=font_label)
        bw = bbox[2] - bbox[0]
        bh = bbox[3] - bbox[1]
        draw.text(
            ((WIDTH - bw) // 2, y + (banner_h - bh) // 2 - bbox[1]),
            banner_text,
            fill=(255, 255, 255),
            font=font_label,
        )
        y += banner_h + 5

        separator = "  \u00b7  "
        for line_subs in footer_lines:
            line_text = separator.join(f"{label} {count}" for label, count in line_subs)
            bbox = draw.textbbox((0, 0), line_text, font=font_label)
            lw = bbox[2] - bbox[0]
            draw.text(
                ((WIDTH - lw) // 2, y),
                line_text,
                fill=(200, 200, 200),
                font=font_label,
            )
            y += line_h

    return img


def _draw_centered(draw: ImageDraw.ImageDraw, text: str, font, fill) -> None:
    """Draw centered text on the dashboard."""
    bbox = draw.textbbox((0, 0), text, font=font)
    ew = bbox[2] - bbox[0]
    draw.text(
        ((WIDTH - ew) // 2, HEIGHT // 2),
        text,
        fill=fill,
        font=font,
    )
