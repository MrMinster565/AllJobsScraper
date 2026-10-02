"""One-time helper: finds your Telegram chat id and saves it to .env.

1. In Telegram, talk to @BotFather, send /newbot, follow the steps, copy the token.
2. Put the token in .env as TELEGRAM_BOT_TOKEN=...
3. Open your new bot in Telegram and send it any message (e.g. "hi").
4. Run:  python setup_telegram.py
"""
from pathlib import Path

from alljobs.config import telegram_creds
from alljobs.telegram_bot import find_chat_id, send_message

token, _ = telegram_creds()
if not token:
    raise SystemExit("Add TELEGRAM_BOT_TOKEN=... to your .env file first.")
chat_id = find_chat_id(token)
if not chat_id:
    raise SystemExit("No messages found. Send any message to your bot in Telegram, then run this again.")

env = Path(".env")
lines = [l for l in env.read_text(encoding="utf-8").splitlines() if not l.startswith("TELEGRAM_CHAT_ID=")]
lines.append(f"TELEGRAM_CHAT_ID={chat_id}")
env.write_text("\n".join(lines) + "\n", encoding="utf-8")
send_message("✅ AllJobs מחובר לטלגרם", token=token, chat_id=chat_id)
print("Done - check Telegram for a confirmation message.")
