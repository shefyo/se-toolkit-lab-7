from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


BOT_DIR = Path(__file__).resolve().parent
REPO_ROOT = BOT_DIR.parent
ENV_SECRET = REPO_ROOT / ".env.bot.secret"
ENV_EXAMPLE = REPO_ROOT / ".env.bot.example"


def load_config() -> dict[str, str | None]:
    if ENV_SECRET.exists():
        load_dotenv(ENV_SECRET)
    elif ENV_EXAMPLE.exists():
        load_dotenv(ENV_EXAMPLE)

    return {
        "BOT_TOKEN": os.getenv("BOT_TOKEN"),
        "LMS_API_URL": os.getenv("LMS_API_URL"),
        "LMS_API_KEY": os.getenv("LMS_API_KEY"),
        "LLM_API_KEY": os.getenv("LLM_API_KEY"),
        "LLM_API_BASE_URL": os.getenv("LLM_API_BASE_URL"),
        "LLM_API_MODEL": os.getenv("LLM_API_MODEL"),
    }
