"""
api/webhook.py — Vercel serverless function.
Telegram calls this endpoint via POST for every incoming message.

Commands handled:
  /cita             → random date idea (any type)
  /cita finde       → weekend idea only
  /cita cotidiana   → weekday idea only
  /proxima          → next planned dates (with fecha set)
  /realizada <#>    → mark date #N as done
  /help             → command list
"""

import json
import os
import random
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from michicator.sheets_client import SheetsClient
from michicator import telegram_client


_HELP_TEXT = (
    "🗓 *Dates con Frida — comandos:*\n\n"
    "/cita — idea aleatoria\n"
    "/cita finde — solo fines de semana\n"
    "/cita cotidiana — solo entre semana\n"
    "/proxima — próximas citas planeadas\n"
    "/realizada <#> — marcar cita como hecha ✅\n"
    "/help — esta ayuda"
)


def _format_idea(idea: dict, show_fecha: bool = False) -> str:
    numero = idea.get("#", "?")
    detalle = str(idea.get("detalle", "")).strip()
    tipo = str(idea.get("tipo", "")).strip().lower()
    referencia = str(idea.get("referencia", "")).strip()
    fecha = str(idea.get("fecha", "")).strip()

    tipo_emoji = {
        "cotidiana": "🌿",
        "finde": "🎉",
        "cotidiana/finde": "✨",
    }.get(tipo, "📍")

    lines = [f"{tipo_emoji} *#{numero} — {detalle}*"]
    if tipo:
        lines.append(f"_{tipo}_")
    if show_fecha and fecha:
        lines.append(f"📅 {fecha}")
    if referencia:
        lines.append(referencia)

    return "\n".join(lines)


def _process_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = str(message["chat"]["id"])
    text = str(message.get("text", "")).strip()

    if not text.startswith("/"):
        return

    parts = text.lower().split()
    # strip @botname suffix (e.g. /cita@michicatorbot → /cita)
    command = parts[0].split("@")[0]

    sheets = SheetsClient()

    if command == "/help":
        telegram_client.send_message(chat_id, _HELP_TEXT)

    elif command == "/cita":
        tipo = parts[1] if len(parts) > 1 else None

        if tipo and tipo not in ("finde", "cotidiana"):
            telegram_client.send_message(
                chat_id,
                "Uso: /cita, /cita finde, o /cita cotidiana",
            )
            return

        ideas = sheets.get_date_ideas(tipo=tipo)
        if not ideas:
            filtro = f" de tipo *{tipo}*" if tipo else ""
            telegram_client.send_message(
                chat_id,
                f"No hay ideas pendientes{filtro} 😅",
            )
            return

        idea = random.choice(ideas)
        telegram_client.send_message(chat_id, _format_idea(idea))

    elif command == "/proxima":
        upcoming = sheets.get_upcoming_dates()
        if not upcoming:
            telegram_client.send_message(
                chat_id,
                "No hay citas planeadas con fecha aún 📅",
            )
            return

        lines = ["📅 *Próximas citas:*\n"]
        for idea in upcoming[:3]:
            lines.append(_format_idea(idea, show_fecha=True))
        telegram_client.send_message(chat_id, "\n\n".join(lines))

    elif command == "/realizada":
        if len(parts) < 2 or not parts[1].isdigit():
            telegram_client.send_message(
                chat_id,
                "Uso: /realizada <número> — ej. /realizada 3",
            )
            return

        numero = int(parts[1])
        found = sheets.mark_date_done(numero)
        if found:
            telegram_client.send_message(chat_id, f"✅ Cita #{numero} marcada como realizada!")
        else:
            telegram_client.send_message(chat_id, f"No encontré la cita #{numero} 🤔")

    else:
        telegram_client.send_message(chat_id, f"Comando no reconocido. Escribe /help para ver opciones.")


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        # Verify Telegram secret token to reject unauthorized requests
        expected_secret = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")
        if expected_secret:
            received = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if received != expected_secret:
                self.send_response(403)
                self.end_headers()
                return

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            update = json.loads(body)
            _process_update(update)
        except Exception as e:
            # Log error but always return 200 so Telegram doesn't retry endlessly
            print(f"[webhook] error processing update: {e}", flush=True)

        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"michicator webhook OK")

    def log_message(self, format, *args):
        pass  # suppress default per-request noise
