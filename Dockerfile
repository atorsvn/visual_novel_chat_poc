FROM python:3.11-slim

WORKDIR /app

# Install build dependencies for Pillow font rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md waifu_config.json ./
COPY visual_novel_chat.py ./
COPY visual_novel_chat ./visual_novel_chat
COPY backgrounds ./backgrounds
COPY fonts ./fonts
COPY sprites ./sprites
COPY ui_elements ./ui_elements
COPY output ./output

RUN pip install --no-cache-dir .

ENV BOT_TOKEN=""
CMD ["python", "-m", "visual_novel_chat"]
