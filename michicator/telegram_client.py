"""
Telegram client — sends a text message to a chat.
Uses the Bot API directly via requests (no heavy library needed).
"""

import os
import requests


_API_BASE = "https://api.telegram.org/bot{token}"


def send_message(chat_id: str, text: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"{_API_BASE.format(token=token)}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
