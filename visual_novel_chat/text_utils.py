"""Utility helpers for handling text rendering in the visual novel UI."""

from __future__ import annotations

import logging
import textwrap
from typing import Any, List

try:
    from PIL import ImageFont
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    ImageFont = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


def wrap_text(text: str, width: int = 30) -> str:
    """Return *text* wrapped at *width* characters per line."""

    wrapper = textwrap.TextWrapper(width=width)
    lines = wrapper.wrap(text=text)
    logger.debug("Wrapped text into %d line(s) with width %d", len(lines), width)
    return "\n".join(lines)


def paginate_text(text: str, lines_per_page: int = 5) -> List[str]:
    """Split *text* into chunks containing *lines_per_page* lines."""

    if lines_per_page <= 0:
        raise ValueError("lines_per_page must be a positive integer")
    lines = text.splitlines() or [""]
    pages = ["\n".join(lines[i : i + lines_per_page]) for i in range(0, len(lines), lines_per_page)]
    logger.debug("Paginated text into %d page(s) with %d lines per page", len(pages), lines_per_page)
    return pages


def get_text_dimensions(text: str, font: Any) -> tuple[int, int]:
    """Return the width and height of *text* for the specified *font*."""

    if ImageFont is None:
        raise ModuleNotFoundError("Pillow is required to measure text dimensions")
    ascent, descent = font.getmetrics()
    bbox = font.getmask(text).getbbox()
    if bbox:
        text_width = bbox[2]
        text_height = bbox[3] + descent
    else:
        text_width, text_height = 0, 0
    logger.debug("Measured text dimensions: %dx%d", text_width, text_height)
    return text_width, text_height
