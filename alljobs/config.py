from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def anthropic_key() -> str | None:
    return os.getenv("ANTHROPIC_API_KEY") or None


def telegram_creds() -> tuple[str | None, str | None]:
    return os.getenv("TELEGRAM_BOT_TOKEN") or None, os.getenv("TELEGRAM_CHAT_ID") or None
