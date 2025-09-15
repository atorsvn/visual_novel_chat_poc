"""Module containing constants shared across the package."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


CONST_POSITION = {
    "left": (-115, 0),
    "center": (108, 0),
    "right": (300, 0),
}

DEFAULT_DB_PATH = "chat_history.db"

logger.debug("Constants module loaded with positions: %s", CONST_POSITION)
