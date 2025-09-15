"""Visual novel UI rendering and Discord view management."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

import discord
from discord.ui import Button, View
from PIL import Image, ImageDraw, ImageFont

from .constants import CONST_POSITION
from .text_utils import get_text_dimensions, paginate_text, wrap_text

logger = logging.getLogger(__name__)


class VisualNovel:
    """Represents the current state of the visual novel overlay."""

    def __init__(self, waifu_config: Dict[str, str], assets_root: Optional[Path] = None) -> None:
        self.waifu_config = waifu_config
        self.prefix = "!"
        self.state = 0
        self.menu_position = 0
        self.waifu_mood = "love"
        self.waifu_chat = "Hello!"
        self.waifu_stats = ""
        self.current_location = "bridge"
        self.waifu_position = CONST_POSITION["center"]
        self.last_interaction = None
        self.images: Dict[str, Image.Image] = {}
        self.views: List[View] = []
        self.waifu_chat_full = ""
        self.waifu_chat_pages: List[str] = []
        self.current_chat_page = 0
        self.assets_root = Path(assets_root) if assets_root else Path(__file__).resolve().parent.parent
        self.output_dir = self.assets_root / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.output_file = self.output_dir / "screen.jpg"

        self.view_configs = self._build_view_configs()
        self.menu_texts = self._build_menu_texts()
        self.render_functions = [
            self.render_chat,
            self.render_map,
            self.render_about,
            self.render_quit,
        ]
        logger.debug("VisualNovel initialised with output directory %s", self.output_dir)

    # -- Setup helpers -------------------------------------------------------

    def load_images(self) -> None:
        """Load sprites, backgrounds and overlays from disk."""

        def load_image(*path_parts: str) -> Image.Image:
            return Image.open(self.assets_root.joinpath(*path_parts))

        self.images["empty"] = load_image("ui_elements", "blank.png")
        self.images["love"] = load_image("sprites", "smile.png")
        self.images["joy"] = load_image("sprites", "delighted.png")
        self.images["anger"] = load_image("sprites", "angry.png")
        self.images["surprise"] = load_image("sprites", "shocked.png")
        self.images["sadness"] = load_image("sprites", "sad.png")
        self.images["fear"] = load_image("sprites", "shocked.png")
        self.images["menu"] = load_image("ui_elements", "overlay_menu.png")
        self.images["map"] = load_image("ui_elements", "overlay_map.png")
        self.images["about"] = load_image("ui_elements", "overlay_about.png")
        self.images["chat"] = load_image("ui_elements", "overlay_chat.png")
        self.images["bridge"] = load_image("backgrounds", "bridge.png")
        self.images["swing"] = load_image("backgrounds", "swing.png")
        self.images["grove"] = load_image("backgrounds", "grove.png")
        self.images["path"] = load_image("backgrounds", "path.png")
        logger.info("Loaded %d visual novel image assets", len(self.images))

    def load_views(self) -> None:
        """Create Discord UI views once the event loop is available."""

        self.views = []
        for view_conf in self.view_configs:
            view = View()
            for btn_conf in view_conf:
                button = Button(
                    label=btn_conf["label"],
                    style=btn_conf["style"],
                    emoji=btn_conf.get("emoji"),
                )
                button.callback = btn_conf["callback"]
                view.add_item(button)
            self.views.append(view)
        logger.debug("Prepared %d Discord UI view(s)", len(self.views))

    # -- Text helpers --------------------------------------------------------

    def prepare_chat_pages(self, response_text: str, width: int = 30, lines_per_page: int = 5) -> List[str]:
        wrapped_text = wrap_text(response_text, width=width)
        pages = paginate_text(wrapped_text, lines_per_page=lines_per_page)
        self.waifu_chat_full = wrapped_text
        self.waifu_chat_pages = pages
        self.current_chat_page = 0
        self.waifu_chat = pages[0]
        logger.debug(
            "Prepared %d chat page(s) for response length %d", len(pages), len(response_text)
        )
        return pages

    def update_waifu_stats(self) -> None:
        self.waifu_stats = (
            f"👰 {self.waifu_config['BOT-NAME']} ♥ {self.waifu_mood} 📍 {self.current_location}"
        )
        logger.debug("Updated waifu stats to '%s'", self.waifu_stats)

    # -- Rendering helpers ---------------------------------------------------

    def _build_view_configs(self) -> List[List[Dict]]:
        return [
            [
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_menu:1053798469984325723>", "callback": self.button_menu_callback},
            ],
            [
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_menu:1053798469984325723>", "callback": self.button_menu_callback},
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_up:1045073082622152735>", "callback": self.button_up_callback},
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_down:1045073143238242335>", "callback": self.button_down_callback},
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_ok:1043819251955400725>", "callback": self.button_menu_ok_callback},
            ],
            [
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_menu:1053798469984325723>", "callback": self.button_menu_callback},
                {"label": "1", "style": discord.ButtonStyle.blurple, "callback": self.button_map_1_callback},
                {"label": "2", "style": discord.ButtonStyle.blurple, "callback": self.button_map_2_callback},
                {"label": "3", "style": discord.ButtonStyle.blurple, "callback": self.button_map_3_callback},
                {"label": "4", "style": discord.ButtonStyle.blurple, "callback": self.button_map_4_callback},
            ],
            [
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_menu:1053798469984325723>", "callback": self.button_menu_callback},
                {"label": "So Cool! Sonuvabitch.", "style": discord.ButtonStyle.blurple, "callback": self.button_map_1_callback},
            ],
            [
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_menu:1053798469984325723>", "callback": self.button_menu_callback},
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_up:1045073082622152735>", "callback": self.button_chat_up_callback},
                {"label": "", "style": discord.ButtonStyle.blurple, "emoji": "<:wht_down:1045073143238242335>", "callback": self.button_chat_down_callback},
            ],
        ]

    def _build_menu_texts(self) -> List[str]:
        return [
            "👉 CHAT\n      MAP\n      ABOUT\n      QUIT",
            "      CHAT\n👉 MAP\n      ABOUT\n      QUIT",
            "      CHAT\n      MAP\n👉 ABOUT\n      QUIT",
            "      CHAT\n      MAP\n      ABOUT\n👉 QUIT",
        ]

    def _prepare_screen(self, overlay_key: Optional[str] = None):
        width, height = 720, 540
        base = self.images["empty"].copy()
        background = self.images[self.current_location]
        base.paste(background, (0, 0), background)
        sprite = self.images[self.waifu_mood]
        base.paste(sprite, self.waifu_position, sprite)
        if overlay_key:
            overlay = self.images[overlay_key]
            base.paste(overlay, (0, 0), overlay)
        draw = ImageDraw.Draw(base)
        font = ImageFont.truetype(str(self.assets_root / "fonts" / "OpenSansEmoji.ttf"), 30, encoding="unic")
        text_width, _ = get_text_dimensions(self.waifu_stats, font)
        draw.text(((width - text_width) / 2, 18), self.waifu_stats, (255, 255, 255), font=font)
        logger.debug("Prepared screen with overlay '%s'", overlay_key)
        return base, draw, font, width

    async def _update_interaction(self, interaction) -> None:
        logger.debug("Updating Discord interaction for state %d", self.state)
        await interaction.message.delete()
        await interaction.message.channel.send(
            file=discord.File(str(self.output_file)),
            view=self.views[self.state],
        )

    async def render_menu(self, interaction) -> None:
        self.last_interaction = interaction
        base, draw, font, width = self._prepare_screen("menu")
        draw.text((27, 91), self.menu_texts[self.menu_position], (255, 255, 255), font=font)
        base.convert("RGB").save(self.output_file)
        await self._update_interaction(interaction)
        logger.info("Rendered menu at position %d", self.menu_position)

    async def render_chat(self, interaction) -> None:
        self.last_interaction = interaction
        text_box_center = 416
        base, draw, font, width = self._prepare_screen("chat")
        bbox = draw.textbbox((0, 0), self.waifu_chat, font=font)
        if bbox:
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = text_height = 0
        draw.text(((width - text_width) / 2, text_box_center - (text_height / 2)), self.waifu_chat, (255, 255, 255), font=font)
        base.convert("RGB").save(self.output_file)
        await self._update_interaction(interaction)
        logger.info("Rendered chat screen for page %d", self.current_chat_page + 1)

    async def render_waifu_chat(self) -> None:
        text_box_center = 416
        base, draw, font, width = self._prepare_screen("chat")
        bbox = draw.textbbox((0, 0), self.waifu_chat, font=font)
        if bbox:
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = text_height = 0
        draw.text(((width - text_width) / 2, text_box_center - (text_height / 2)), self.waifu_chat, (255, 255, 255), font=font)
        if len(self.waifu_chat_pages) > 1:
            page_indicator = f"Page {self.current_chat_page + 1}/{len(self.waifu_chat_pages)}"
            draw.text((width - 150, text_box_center + (text_height / 2) + 10), page_indicator, (255, 255, 255), font=font)
        base.convert("RGB").save(self.output_file)
        logger.debug("Rendered waifu chat page %d", self.current_chat_page + 1)

    async def render_about(self, interaction) -> None:
        self.state = 3
        base, _, _, _ = self._prepare_screen("about")
        base.convert("RGB").save(self.output_file)
        await self._update_interaction(interaction)
        logger.info("Rendered about screen")

    async def render_map(self, interaction) -> None:
        self.last_interaction = interaction
        self.state = 2
        base, _, _, _ = self._prepare_screen("map")
        base.convert("RGB").save(self.output_file)
        await self._update_interaction(interaction)
        logger.info("Rendered map screen at location %s", self.current_location)

    async def render_quit(self, interaction) -> None:
        logger.info("Rendering quit confirmation message")
        await interaction.message.delete()
        await interaction.message.channel.send("Thanks for trying out the demo!")

    async def start(self) -> None:
        base, _, _, _ = self._prepare_screen("chat")
        base.convert("RGB").save(self.output_file)
        logger.debug("Initial screen prepared at start")

    # -- Button callbacks ----------------------------------------------------

    async def button_menu_callback(self, interaction) -> None:
        self.state = 1
        self.menu_position = 0
        await self.render_menu(interaction)
        logger.debug("Menu button pressed; state=%d", self.state)

    async def button_up_callback(self, interaction) -> None:
        if self.menu_position > 0:
            self.menu_position -= 1
        await self.render_menu(interaction)
        logger.debug("Menu up button pressed; position=%d", self.menu_position)

    async def button_down_callback(self, interaction) -> None:
        if self.menu_position < len(self.menu_texts) - 1:
            self.menu_position += 1
        await self.render_menu(interaction)
        logger.debug("Menu down button pressed; position=%d", self.menu_position)

    async def button_menu_ok_callback(self, interaction) -> None:
        self.state = self.menu_position
        await self.render_functions[self.state](interaction)
        logger.debug("Menu OK button pressed; new state=%d", self.state)

    async def button_map_1_callback(self, interaction) -> None:
        self.state = 0
        self.current_location = "bridge"
        self.waifu_config["SITUATION"] = (
            "Waifu loves her Senpai. They are having a conversation in a park at the bridge"
        )
        await self.render_functions[self.state](interaction)
        logger.info("Map button 1 selected; location set to %s", self.current_location)

    async def button_map_2_callback(self, interaction) -> None:
        self.state = 0
        self.current_location = "swing"
        self.waifu_config["SITUATION"] = (
            "Waifu loves her Senpai. They are having a conversation in a park at the swing"
        )
        await self.render_functions[self.state](interaction)
        logger.info("Map button 2 selected; location set to %s", self.current_location)

    async def button_map_3_callback(self, interaction) -> None:
        self.state = 0
        self.current_location = "grove"
        self.waifu_config["SITUATION"] = (
            "Waifu loves her Senpai. They are having a conversation in a park at the grove"
        )
        await self.render_functions[self.state](interaction)
        logger.info("Map button 3 selected; location set to %s", self.current_location)

    async def button_map_4_callback(self, interaction) -> None:
        self.state = 0
        self.current_location = "path"
        self.waifu_config["SITUATION"] = (
            "Waifu loves her Senpai. They are having a conversation in a park at a path leading to woods"
        )
        await self.render_functions[self.state](interaction)
        logger.info("Map button 4 selected; location set to %s", self.current_location)

    async def button_chat_up_callback(self, interaction) -> None:
        if self.current_chat_page > 0:
            self.current_chat_page -= 1
            self.waifu_chat = self.waifu_chat_pages[self.current_chat_page]
            await self.render_waifu_chat()
        await self._update_interaction(interaction)
        logger.debug("Chat page moved up to %d", self.current_chat_page)

    async def button_chat_down_callback(self, interaction) -> None:
        if self.current_chat_page < len(self.waifu_chat_pages) - 1:
            self.current_chat_page += 1
            self.waifu_chat = self.waifu_chat_pages[self.current_chat_page]
            await self.render_waifu_chat()
        await self._update_interaction(interaction)
        logger.debug("Chat page moved down to %d", self.current_chat_page)
