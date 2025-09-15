# Visual Novel Chat Bot

This project contains a Discord bot that renders a visual novel style UI and interacts with users via large language models. The codebase has been refactored into a modular Python package with automated tests and Docker support.

## Features

- Discord bot that renders a visual novel overlay using Pillow.
- Conversation persistence backed by SQLite.
- Emotion detection powered by a Transformers classifier.
- Modular Python package with pytest test suite.
- Docker image for reproducible deployments.

## Getting Started

### Prerequisites

- Python 3.10 or newer
- [Ollama](https://ollama.ai/) running locally with the `llama3.2` model
- A Discord bot token

### Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Copy `waifu_config.json` and update the `BOT-TOKEN` value with your Discord bot token.

### Running the Bot

```bash
python -m visual_novel_chat
```

This command will download the required NLTK corpora on first run, start the Discord bot and connect to Ollama for responses.

### Running Tests

```bash
pytest
```

## Docker

A Dockerfile is provided for containerised deployments. Build and run it with:

```bash
docker build -t visual-novel-chat .
docker run --env BOT_TOKEN=your-token --env OLLAMA_HOST=host.docker.internal:11434 visual-novel-chat
```

The container uses the packaged configuration file. Override the bot token by setting the `BOT_TOKEN` environment variable or mounting a custom `waifu_config.json`.

## Project Structure

```
visual_novel_chat/
  ai.py            # Emotion classification and model orchestration
  bot.py           # Discord bot creation and entry point
  config.py        # Configuration loader
  database.py      # SQLite persistence layer
  text_utils.py    # Text wrapping and pagination helpers
  visual_novel.py  # Rendering and Discord view logic
```

Tests live in the `tests/` directory and cover the utility layers.

## License

This repository is provided as-is for demonstration purposes.
