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

    # Markdown parsing can fail with 400 if the text contains unescaped special
    # characters. Retry as plain text so the message is never lost.
    if response.status_code == 400:
        print(f"⚠ Telegram rechazó el mensaje con parse_mode=Markdown (400): {response.text}")
        print("  Reintentando sin parse_mode...")
        payload.pop("parse_mode", None)
        response = requests.post(url, json=payload, timeout=15)

    response.raise_for_status()

    data = response.json()
    if not data.get("ok"):
        raise RuntimeError(f"Telegram API error: {data}")
