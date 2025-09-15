"""Thin wrapper around the Ollama Python client with logging."""

from __future__ import annotations

import logging
from typing import Any, Iterable

logger = logging.getLogger(__name__)


def _get_client() -> Any:
    """Return the Ollama client module, importing it lazily."""

    try:
        import ollama  # type: ignore[import]
    except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency
        logger.error("The 'ollama' package is not installed", exc_info=exc)
        raise
    logger.debug("Ollama client module imported successfully")
    return ollama


def chat(*, model: str, messages: Iterable[dict], **kwargs: Any) -> Any:
    """Proxy chat requests to the Ollama client with logging."""

    message_list = list(messages)
    logger.info(
        "Sending chat request to Ollama model '%s' with %d message(s)",
        model,
        len(message_list),
    )
    client = _get_client()
    response = client.chat(model=model, messages=message_list, **kwargs)
    logger.debug("Received chat response from Ollama model '%s'", model)
    return response


__all__ = ["chat"]
