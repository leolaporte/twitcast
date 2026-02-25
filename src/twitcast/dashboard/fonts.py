"""Font loading with fallback."""

from PIL import ImageFont

BOLD_PATHS = [
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
]

REGULAR_PATHS = [
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
]


def _try_load(paths: list[str], size: int) -> ImageFont.FreeTypeFont | None:
    for path in paths:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return None


def load_fonts() -> tuple:
    """Load dashboard fonts.

    Returns (font_header, font_code, font_label, font_title, font_date).
    """
    font_header = _try_load(BOLD_PATHS, 28)
    font_code = _try_load(BOLD_PATHS, 22)
    font_label = _try_load(BOLD_PATHS, 18)
    font_title = _try_load(BOLD_PATHS, 16)
    font_date = _try_load(REGULAR_PATHS, 16)

    if font_header is None:
        font_header = ImageFont.load_default()
        font_label = font_header
    if font_code is None:
        font_code = font_label
    if font_title is None:
        font_title = font_label
    if font_date is None:
        font_date = font_label

    return font_header, font_code, font_label, font_title, font_date
