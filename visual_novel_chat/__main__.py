"""Allow running ``python -m visual_novel_chat`` to start the bot."""

from __future__ import annotations

import logging

from .bot import main

logger = logging.getLogger(__name__)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Launching visual_novel_chat via module execution")
    main()
