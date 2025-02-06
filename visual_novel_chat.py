import discord
from discord.ui import Button, View
from discord.ext import commands
from PIL import Image, ImageFont, ImageDraw
import textwrap
import json
import re
import sqlite3
import nltk
from transformers import pipeline
from ollama import chat, ChatResponse

# Download necessary NLTK data
nltk.download('stopwords')
nltk.download('punkt')
nltk.download('wordnet')

# --- SQLite Conversation History Utilities ---

DB_PATH = 'chat_history.db'

def init_db():
    """Initialize the SQLite database and create the conversation table if needed."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            role TEXT,
            content TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_message(user_id: str, role: str, content: str):
    """Insert a new message into the conversation table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO conversation (user_id, role, content)
        VALUES (?, ?, ?)
    ''', (user_id, role, content))
    conn.commit()
    conn.close()

def get_conversation(user_id: str):
    """
    Retrieve the conversation for the given user_id ordered by insertion.
    Returns a list of dictionaries with keys: "role" and "content".
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT role, content FROM conversation
        WHERE user_id = ?
        ORDER BY id ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return [{"role": row[0], "content": row[1]} for row in rows]

def prune_conversation(user_id: str, max_messages: int = 9):
    """
    Ensure that the conversation for the given user_id contains at most max_messages rows.
    The first message (with role "system") is always kept and is never deleted.
    Additional messages beyond the last (max_messages - 1) are removed.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, role FROM conversation
        WHERE user_id = ?
        ORDER BY id ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    # rows is a list of tuples (id, role). We always keep the first row (system prompt).
    if len(rows) > max_messages:
        # Keep the first row and the last (max_messages - 1) rows.
        ids_to_keep = {rows[0][0]} | {row[0] for row in rows[-(max_messages - 1):]}
        # Delete any row not in ids_to_keep.
        ids_to_delete = [row[0] for row in rows if row[0] not in ids_to_keep]
        if ids_to_delete:
            cursor.executemany('''
                DELETE FROM conversation WHERE id = ?
            ''', [(id_val,) for id_val in ids_to_delete])
            conn.commit()
    conn.close()

# --- Global Constants and Utility Functions ---

CONST_POSITION = {
    "left": (-115, 0),
    "center": (108, 0),
    "right": (300, 0)
}

# Initialize the Hugging Face emotion classifier.
classifier = pipeline(
    "text-classification",
    model='bhadresh-savani/distilbert-base-uncased-finetuned-emotion',
    return_all_scores=False
)

def get_emotion(text: str):
    """Return the emotion prediction for the given text."""
    return classifier(text)

def waifu_text_wrap(text_string: str, width: int = 30) -> str:
    """Wrap the text to the given width and return it as a single string."""
    wrapper = textwrap.TextWrapper(width=width)
    lines = wrapper.wrap(text=text_string)
    return "\n".join(lines)

def get_text_dimensions(text_string: str, font: ImageFont.FreeTypeFont):
    """Return the (width, height) of the given text using the provided font."""
    ascent, descent = font.getmetrics()
    bbox = font.getmask(text_string).getbbox()
    if bbox:
        text_width = bbox[2]
        text_height = bbox[3] + descent
    else:
        text_width, text_height = 0, 0
    return (text_width, text_height)

# --- AI Query with Conversation Context using Ollama and SQLite ---

def waifu_ai_query(query: str, user_id, user_name, waifu_config: dict) -> str:
    """
    Retrieve conversation context from SQLite, append the user's query,
    call the Ollama API with the full context (system prompt + up to 8 messages),
    then store the assistant's response and return it.
    """
    # Ensure conversation exists for this user.
    conversation = get_conversation(str(user_id))
    if not conversation:
        # Insert system prompt (never deleted)
        system_prompt = waifu_config.get("SYSTEM_PROMPT", "You are an anime waifu named Gwen.")
        add_message(str(user_id), "system", system_prompt)
        conversation = get_conversation(str(user_id))
    
    # Append the user's new query.
    add_message(str(user_id), "user", query)
    prune_conversation(str(user_id))
    conversation = get_conversation(str(user_id))
    
    # Prepare the messages list for the Ollama API.
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation]
    
    # Call the Ollama API.
    response: ChatResponse = chat(model='llama3.2', messages=messages)
    
    # Store the assistant's response.
    add_message(str(user_id), "assistant", response.message.content)
    prune_conversation(str(user_id))
    
    return response.message.content

# --- Visual Novel Class Definition ---

class VisualNovel:
    def __init__(self, waifu_config: dict):
        self.waifu_config = waifu_config
        self.prefix = "!"
        self.state = 0
        self.menu_position = 0
        self.waifu_mood = "love"
        self.waifu_chat = "Hello!"
        self.waifu_stats = ""
        self.current_location = "bridge"
        self.waifu_position = CONST_POSITION['center']
        self.last_interaction = None
        self.images = {}
        self.views = []  # Will be loaded after the event loop starts.
        self.view_configs = [
            # View 0: initial view with just the menu button
            [
                {"label": "",
                 "style": discord.ButtonStyle.blurple,
                 "emoji": "<:wht_menu:1053798469984325723>",
                 "callback": self.button_menu_callback}
            ],
            # View 1: menu navigation view
            [
                {"label": "",
                 "style": discord.ButtonStyle.blurple,
                 "emoji": "<:wht_menu:1053798469984325723>",
                 "callback": self.button_menu_callback},
                {"label": "",
                 "style": discord.ButtonStyle.blurple,
                 "emoji": "<:wht_up:1045073082622152735>",
                 "callback": self.button_up_callback},
                {"label": "",
                 "style": discord.ButtonStyle.blurple,
                 "emoji": "<:wht_down:1045073143238242335>",
                 "callback": self.button_down_callback},
                {"label": "",
                 "style": discord.ButtonStyle.blurple,
                 "emoji": "<:wht_ok:1043819251955400725>",
                 "callback": self.button_menu_ok_callback}
            ],
            # View 2: map selection view
            [
                {"label": "",
                 "style": discord.ButtonStyle.blurple,
                 "emoji": "<:wht_menu:1053798469984325723>",
                 "callback": self.button_menu_callback},
                {"label": "1",
                 "style": discord.ButtonStyle.blurple,
                 #"emoji": "",
                 "callback": self.button_map_1_callback},
                {"label": "2",
                 "style": discord.ButtonStyle.blurple,
                 #"emoji": "",
                 "callback": self.button_map_2_callback},
                {"label": "3",
                 "style": discord.ButtonStyle.blurple,
                 #"emoji": "",
                 "callback": self.button_map_3_callback},
                {"label": "4",
                 "style": discord.ButtonStyle.blurple,
                 #"emoji": "",
                 "callback": self.button_map_4_callback}
            ],
            # View 3: about screen view
            [
                {"label": "",
                 "style": discord.ButtonStyle.blurple,
                 "emoji": "<:wht_menu:1053798469984325723>",
                 "callback": self.button_menu_callback},
                {"label": "So Cool! Sonuvabitch.",
                 "style": discord.ButtonStyle.blurple,
                 #"emoji": "",
                 "callback": self.button_map_1_callback}
            ]
        ]
        self.menu_texts = [
            "👉 CHAT\n      MAP\n      ABOUT\n      QUIT",
            "      CHAT\n👉 MAP\n      ABOUT\n      QUIT",
            "      CHAT\n      MAP\n👉 ABOUT\n      QUIT",
            "      CHAT\n      MAP\n      ABOUT\n👉 QUIT"
        ]
        # Render functions correspond to: [chat, map, about, quit]
        self.render_functions = [
            self.render_chat,
            self.render_map,
            self.render_about,
            self.render_quit,
        ]
    
    def load_images(self):
        """Load all required images from disk."""
        self.images['empty'] = Image.open('ui_elements/blank.png')
        self.images['love'] = Image.open('sprites/smile.png')
        self.images['joy'] = Image.open('sprites/delighted.png')
        self.images['anger'] = Image.open('sprites/angry.png')
        self.images['surprise'] = Image.open('sprites/shocked.png')
        self.images['sadness'] = Image.open('sprites/sad.png')
        self.images['fear'] = Image.open('sprites/shocked.png')
        self.images['menu'] = Image.open('ui_elements/overlay_menu.png')
        self.images['map'] = Image.open('ui_elements/overlay_map.png')
        self.images['about'] = Image.open('ui_elements/overlay_about.png')
        self.images['chat'] = Image.open('ui_elements/overlay_chat.png')
        self.images['bridge'] = Image.open('backgrounds/bridge.png')
        self.images['swing'] = Image.open('backgrounds/swing.png')
        self.images['grove'] = Image.open('backgrounds/grove.png')
        self.images['path'] = Image.open('backgrounds/path.png')
    
    def _prepare_screen(self, overlay_key: str = None):
        """
        Create the base image by pasting the background (current location),
        the waifu sprite (based on mood) and an optional overlay.
        Also draws the waifu stats at the top center.
        """
        W, H = 720, 540
        base = self.images['empty'].copy()
        base.paste(self.images[self.current_location], (0, 0), self.images[self.current_location])
        base.paste(self.images[self.waifu_mood], self.waifu_position, self.images[self.waifu_mood])
        if overlay_key:
            base.paste(self.images[overlay_key], (0, 0), self.images[overlay_key])
        draw = ImageDraw.Draw(base)
        font = ImageFont.truetype("fonts/OpenSansEmoji.ttf", 30, encoding='unic')
        text_width, _ = get_text_dimensions(self.waifu_stats, font)
        draw.text(((W - text_width) / 2, 18), self.waifu_stats, (255, 255, 255), font=font)
        return base, draw, font, W, H

    async def _update_interaction(self, interaction):
        """Delete the old message and send the updated screen image."""
        await interaction.message.delete()
        await interaction.message.channel.send(
            file=discord.File('output/screen.jpg'),
            view=self.views[self.state]
        )

    async def render_menu(self, interaction):
        """Render the menu screen."""
        self.last_interaction = interaction
        base, draw, font, W, H = self._prepare_screen("menu")
        draw.text((27, 91), self.menu_texts[self.menu_position], (255, 255, 255), font=font)
        base.convert('RGB').save('output/screen.jpg')
        await self._update_interaction(interaction)
    
    async def render_chat(self, interaction):
        """Render the chat screen with unwrapped text."""
        self.last_interaction = interaction
        tb_center = 416
        base, draw, font, W, H = self._prepare_screen("chat")
        bbox = draw.textbbox((0, 0), self.waifu_chat, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(((W - text_width) / 2, tb_center - (text_height / 2)),
                  self.waifu_chat, (255, 255, 255), font=font)
        base.convert('RGB').save('output/screen.jpg')
        await self._update_interaction(interaction)
    
    async def render_waifu_chat(self):
        """Render a chat screen with wrapped text (without updating an interaction)."""
        tb_center = 416
        base, draw, font, W, H = self._prepare_screen("chat")
        wrapped_text = waifu_text_wrap(self.waifu_chat)
        bbox = draw.textbbox((0, 0), wrapped_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.text(((W - text_width) / 2, tb_center - (text_height / 2)),
                  wrapped_text, (255, 255, 255), font=font)
        base.convert('RGB').save('output/screen.jpg')
    
    async def render_about(self, interaction):
        """Render the about screen."""
        self.state = 3
        base, _, _, _, _ = self._prepare_screen("about")
        base.convert('RGB').save('output/screen.jpg')
        await self._update_interaction(interaction)
    
    async def render_map(self, interaction):
        """Render the map screen."""
        self.last_interaction = interaction
        self.state = 2
        base, _, _, _, _ = self._prepare_screen("map")
        base.convert('RGB').save('output/screen.jpg')
        await self._update_interaction(interaction)
    
    async def render_quit(self, interaction):
        """Render the quit screen (simply ends the demo)."""
        await interaction.message.delete()
        await interaction.message.channel.send("Thanks for trying out the demo!")
    
    async def start(self):
        """Initial screen preparation (without sending a message)."""
        base, _, _, _, _ = self._prepare_screen("chat")
        base.convert('RGB').save('output/screen.jpg')
    
    async def update_waifu_stats(self):
        """Update the waifu stats string displayed on screen."""
        self.waifu_stats = f"👰 {self.waifu_config['BOT-NAME']} ♥ {self.waifu_mood} 📍 {self.current_location}"
    
    def load_views(self):
        """Create the discord UI views from the view configuration.
           This function is called once the event loop is running.
        """
        self.views = []
        for view_conf in self.view_configs:
            view = View()
            for btn_conf in view_conf:
                btn = Button(
                    label=btn_conf["label"],
                    style=btn_conf["style"],
                    emoji=btn_conf.get("emoji")
                )
                btn.callback = btn_conf["callback"]
                view.add_item(btn)
            self.views.append(view)
    
    # --- Button Callback Methods ---
    
    async def button_menu_callback(self, interaction):
        self.state = 1
        self.menu_position = 0
        await self.render_menu(interaction)
    
    async def button_up_callback(self, interaction):
        if self.menu_position > 0:
            self.menu_position -= 1
        await self.render_menu(interaction)
    
    async def button_down_callback(self, interaction):
        if self.menu_position < len(self.menu_texts) - 1:
            self.menu_position += 1
        await self.render_menu(interaction)
    
    async def button_menu_ok_callback(self, interaction):
        self.state = self.menu_position
        await self.render_functions[self.state](interaction)
    
    async def button_map_1_callback(self, interaction):
        self.state = 0
        self.current_location = 'bridge'
        self.waifu_config['SITUATION'] = (
            "Waifu loves her Senpai. They are having a conversation in a park at the bridge"
        )
        await self.render_functions[self.state](interaction)
    
    async def button_map_2_callback(self, interaction):
        self.state = 0
        self.current_location = 'swing'
        self.waifu_config['SITUATION'] = (
            "Waifu loves her Senpai. They are having a conversation in a park at the swing"
        )
        await self.render_functions[self.state](interaction)
    
    async def button_map_3_callback(self, interaction):
        self.state = 0
        self.current_location = 'grove'
        self.waifu_config['SITUATION'] = (
            "Waifu loves her Senpai. They are having a conversation in a park at the grove"
        )
        await self.render_functions[self.state](interaction)
    
    async def button_map_4_callback(self, interaction):
        self.state = 0
        self.current_location = 'path'
        self.waifu_config['SITUATION'] = (
            "Waifu loves her Senpai. They are having a conversation in a park at a path leading to woods"
        )
        await self.render_functions[self.state](interaction)

# --- Bot Setup and Commands ---

# Initialize the SQLite database.
init_db()

with open('waifu_config.json') as f:
    waifu_config = json.load(f)

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Create our VisualNovel instance and load images.
vn = VisualNovel(waifu_config)
vn.load_images()
# Do not load views here; we'll do that once the event loop is running.

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    vn.load_views()

@bot.command()
async def vnc_start(ctx):
    await vn.update_waifu_stats()
    await vn.start()
    await ctx.send(
        file=discord.File('video/splash.mp4'),
        view=vn.views[vn.state]
    )

@bot.command()
async def gwen(ctx):
    vn.state = 0
    query = re.sub(r"!gwen\s+", "", ctx.message.content)
    # Use the Ollama chat API with conversation history from SQLite.
    response = waifu_ai_query(query, ctx.message.author.id, ctx.message.author.name, waifu_config)
    emotions = get_emotion(response)
    if emotions[0]["score"] > 0.5:
        vn.waifu_mood = emotions[0]["label"]
    else:
        vn.waifu_mood = "love"
    await vn.update_waifu_stats()
    wrapped_text = waifu_text_wrap(response)
    # Limit to the first 5 lines.
    vn.waifu_chat = "\n".join(wrapped_text.splitlines()[:5])
    await vn.render_waifu_chat()
    await ctx.send(
        file=discord.File('output/screen.jpg'),
        view=vn.views[vn.state]
    )

bot.run(waifu_config['BOT-TOKEN'])
