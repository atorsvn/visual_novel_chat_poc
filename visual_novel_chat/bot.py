"""Discord bot setup for the visual novel chat experience."""

from __future__ import annotations

import logging
import os
import re
from typing import Optional

import discord
from discord.ext import commands

from .ai import AiResponder, EmotionClassifier, ensure_nltk_data
from .config import load_config
from .constants import DEFAULT_DB_PATH
from .database import ConversationHistory
from .visual_novel import VisualNovel

logger = logging.getLogger(__name__)


def create_bot(
    config: dict,
    history: Optional[ConversationHistory] = None,
    responder: Optional[AiResponder] = None,
    classifier: Optional[EmotionClassifier] = None,
) -> commands.Bot:
    """Create and configure the Discord bot instance."""

    history = history or ConversationHistory(DEFAULT_DB_PATH)
    responder = responder or AiResponder(history)
    classifier = classifier or EmotionClassifier()

    logger.info("Creating Discord bot with prefix '!' and intents for message content")

    intents = discord.Intents.default()
    intents.message_content = True
    bot = commands.Bot(command_prefix="!", intents=intents)

    visual_novel = VisualNovel(config)
    visual_novel.load_images()
    logger.debug("Visual novel assets loaded during bot initialisation")

    @bot.event
    async def on_ready() -> None:
        logger.info("Discord bot ready as %s", bot.user)
        visual_novel.load_views()
        logger.debug("Discord UI views prepared")

    @bot.command()
    async def gwen(ctx) -> None:
        logger.info("Received !gwen command from user %s", ctx.message.author.id)
        visual_novel.state = 0
        query = re.sub(r"!gwen\s+", "", ctx.message.content)
        waifu_location = (
            "```gwen-data\n\n"
            f"{{'current-location': '{visual_novel.current_location}', 'current-user' : {ctx.message.author.name}\n}}```"
        )
        response = responder.query(waifu_location + query, ctx.message.author.id, ctx.message.author.name, config)
        prediction = classifier.predict(response)

        if prediction["score"] > 0.5:
            visual_novel.waifu_mood = prediction["label"]
        else:
            visual_novel.waifu_mood = "love"

        logger.debug("Predicted emotion %s with score %.3f", prediction["label"], prediction["score"])

        visual_novel.update_waifu_stats()

        pages = visual_novel.prepare_chat_pages(response)
        visual_novel.state = 4 if len(pages) > 1 else 0
        await visual_novel.render_waifu_chat()

        await ctx.send(
            file=discord.File(str(visual_novel.output_file)),
            view=visual_novel.views[visual_novel.state],
        )

        logger.info("Sent response to user %s with %d page(s)", ctx.message.author.id, len(pages))

    return bot


def main(config_path: str = "waifu_config.json") -> None:
    """Entry point used by the command line and Docker image."""

    config = load_config(config_path)
    ensure_nltk_data()
    bot = create_bot(config)
    bot_token = os.getenv("BOT_TOKEN", config.get("BOT-TOKEN"))
    if not bot_token:
        raise KeyError("BOT-TOKEN missing from configuration and BOT_TOKEN env var not set")
    logger.info("Starting Discord bot using provided token")
    bot.run(bot_token)


__all__ = ["create_bot", "main"]
