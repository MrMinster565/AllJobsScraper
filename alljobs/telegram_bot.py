"""Minimal Telegram Bot API client (no extra dependencies beyond requests)."""
from __future__ import annotations

import requests

from .config import telegram_creds

API = "https://api.telegram.org/bot{token}/{method}"


def _call(token: str, method: str, **params) -> dict:
    r = requests.post(API.format(token=token, method=method), json=params, timeout=30)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram error: {data.get('description', r.text)}")
    return data["result"]


def find_chat_id(token: str) -> str | None:
    """After you send any message to your bot, this returns your chat id."""
    updates = _call(token, "getUpdates")
    for u in reversed(updates):
        msg = u.get("message") or u.get("channel_post")
        if msg:
            return str(msg["chat"]["id"])
    return None


def send_message(text: str, token: str | None = None, chat_id: str | None = None) -> None:
    env_token, env_chat = telegram_creds()
    token, chat_id = token or env_token, chat_id or env_chat
    if not token or not chat_id:
        raise RuntimeError("Telegram is not set up (TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID missing in .env)")
    for i in range(0, len(text), 4000):  # Telegram's limit is 4096 chars per message
        _call(token, "sendMessage", chat_id=chat_id, text=text[i : i + 4000], disable_web_page_preview=True)
