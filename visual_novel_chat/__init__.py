"""Core package for the Visual Novel Discord chat bot."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

__all__ = [
    "AiResponder",
    "ConversationHistory",
    "EmotionClassifier",
    "VisualNovel",
    "create_bot",
    "ensure_nltk_data",
    "load_config",
    "main",
]

logger = logging.getLogger(__name__)


def __getattr__(name: str) -> Any:  # pragma: no cover - thin import wrapper
    logger.debug("Lazy-loading attribute '%s' from package", name)
    if name in {"create_bot", "main"}:
        module = import_module(".bot", __name__)
    elif name in {"AiResponder", "EmotionClassifier", "ensure_nltk_data"}:
        module = import_module(".ai", __name__)
    elif name == "ConversationHistory":
        module = import_module(".database", __name__)
    elif name == "VisualNovel":
        module = import_module(".visual_novel", __name__)
    elif name == "load_config":
        module = import_module(".config", __name__)
    else:  # pragma: no cover - defensive
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    return getattr(module, name)


def __dir__() -> list[str]:  # pragma: no cover - thin wrapper
    logger.debug("Listing available attributes for package")
    return sorted(__all__)
