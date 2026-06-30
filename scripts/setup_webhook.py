"""
setup_webhook.py — registers the Vercel webhook URL with Telegram and sets bot commands.

Usage (run once after deploying to Vercel):
  TELEGRAM_BOT_TOKEN=... WEBHOOK_URL=https://your-app.vercel.app/api/webhook python scripts/setup_webhook.py

Optional env var:
  TELEGRAM_WEBHOOK_SECRET — shared secret for request verification (recommended)
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
import requests

load_dotenv()


def _api(token: str, method: str, payload: dict) -> dict:
    url = f"https://api.telegram.org/bot{token}/{method}"
    resp = requests.post(url, json=payload, timeout=15)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    webhook_url = os.environ["WEBHOOK_URL"]
    secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")

    # 1. Register webhook URL
    payload: dict = {"url": webhook_url, "allowed_updates": ["message"]}
    if secret:
        payload["secret_token"] = secret

    data = _api(token, "setWebhook", payload)
    if data.get("ok"):
        print(f"✅ Webhook registrado: {webhook_url}")
    else:
        print(f"❌ Error registrando webhook: {data}")
        sys.exit(1)

    # 2. Register command menu (shows up when users type / in Telegram)
    commands = [
        {"command": "cita",      "description": "Idea de cita aleatoria (o: cita finde / cita cotidiana)"},
        {"command": "proxima",   "description": "Ver las próximas citas planeadas"},
        {"command": "realizada", "description": "Marcar una cita como realizada (ej: /realizada 3)"},
        {"command": "nueva",     "description": "Agregar una nueva idea de cita"},
        {"command": "cancion",   "description": "Agregar una canción a la lista"},
        {"command": "help",      "description": "Ver todos los comandos disponibles"},
    ]
    data = _api(token, "setMyCommands", {"commands": commands})
    if data.get("ok"):
        print("✅ Comandos registrados en BotFather")
    else:
        print(f"❌ Error registrando comandos: {data}")
        sys.exit(1)


if __name__ == "__main__":
    main()
