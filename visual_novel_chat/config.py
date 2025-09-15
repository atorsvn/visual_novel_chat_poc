"""Configuration helpers for the Visual Novel chat bot."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

DEFAULT_CONFIG_PATH = Path("waifu_config.json")

logger = logging.getLogger(__name__)


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Dict[str, Any]:
    """Load the bot configuration from *path*.

    Parameters
    ----------
    path:
        Path to the configuration JSON file. Relative paths are resolved with
        respect to the current working directory.
    """

    config_path = Path(path)
    logger.info("Loading configuration from %s", config_path)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    logger.debug("Configuration loaded with keys: %s", sorted(config.keys()))
    return config
