"""
api/webhook.py — Vercel serverless function.
Telegram calls this endpoint via POST for every incoming message.

Commands handled:
  /cita             → random date idea (any type)
  /cita finde       → weekend idea only
  /cita cotidiana   → weekday idea only
  /proxima          → next planned dates (with fecha set)
  /realizada <#>    → mark date #N as done
  /nueva            → conversational flow to add a date idea
  /cancion          → conversational flow to add a song
  /help             → command list
"""

import json
import os
import random
import re
import sys
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from michicator.sheets_client import SheetsClient
from michicator import telegram_client


_HELP_TEXT = (
    "🗓 *Comandos disponibles:*\n\n"
    "/cita — idea de cita aleatoria\n"
    "/cita finde — solo fines de semana\n"
    "/cita cotidiana — solo entre semana\n"
    "/proxima — próximas citas planeadas\n"
    "/realizada <#> — marcar cita como hecha ✅\n"
    "/nueva — agregar una idea de cita\n"
    "/cancion — agregar una canción\n"
    "/help — esta ayuda"
)

# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

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


def _extract_spotify_id(url: str) -> str:
    match = re.search(r"spotify\.com/track/([A-Za-z0-9]+)", url)
    return match.group(1) if match else ""


# ------------------------------------------------------------------ #
#  Conversational flows                                                #
# ------------------------------------------------------------------ #

def _start_nueva(chat_id: str, sheets: SheetsClient) -> None:
    sheets.set_conv_state(chat_id, {"flow": "nueva", "step": "detalle", "data": {}})
    telegram_client.send_message(chat_id, "🗓 *Nueva idea de cita*\n\n¿Qué quieren hacer? Describe la idea:")


def _start_cancion(chat_id: str, sheets: SheetsClient) -> None:
    sheets.set_conv_state(chat_id, {"flow": "cancion", "step": "url", "data": {}})
    telegram_client.send_message(chat_id, "🎵 *Nueva canción*\n\n¿Cuál es el link de Spotify?")


def _continue_nueva(chat_id: str, text: str, state: dict, sheets: SheetsClient) -> None:
    step = state["step"]
    data = state["data"]

    if step == "detalle":
        data["detalle"] = text.strip()
        state.update({"step": "tipo", "data": data})
        sheets.set_conv_state(chat_id, state)
        telegram_client.send_message(
            chat_id,
            "¿Para cuándo es? Responde:\n"
            "*cotidiana* — miércoles o entre semana\n"
            "*finde* — viernes, sábado o domingo\n"
            "*ambas* — cualquier día sirve",
        )

    elif step == "tipo":
        tipo_map = {"cotidiana": "cotidiana", "finde": "finde", "ambas": "cotidiana/finde"}
        tipo = tipo_map.get(text.lower().strip())
        if not tipo:
            telegram_client.send_message(chat_id, "Escribe *cotidiana*, *finde* o *ambas*:")
            return
        data["tipo"] = tipo
        state.update({"step": "referencia", "data": data})
        sheets.set_conv_state(chat_id, state)
        telegram_client.send_message(
            chat_id,
            "¿Tienes un link de referencia?\n(Google Maps, TikTok, YouTube... o escribe *no*)",
        )

    elif step == "referencia":
        data["referencia"] = "" if text.lower().strip() == "no" else text.strip()
        sheets.add_date_idea(data["detalle"], data["tipo"], data.get("referencia", ""))
        sheets.clear_conv_state(chat_id)
        telegram_client.send_message(chat_id, "✅ ¡Guardado en *Dates con Frida*! 🗓")


def _continue_cancion(chat_id: str, text: str, state: dict, sheets: SheetsClient) -> None:
    step = state["step"]
    data = state["data"]

    if step == "url":
        url = text.strip()
        spotify_id = _extract_spotify_id(url)
        data["url"] = url
        data["spotify_id"] = spotify_id
        state.update({"step": "titulo", "data": data})
        sheets.set_conv_state(chat_id, state)
        telegram_client.send_message(chat_id, "¿Cómo se llama la canción?")

    elif step == "titulo":
        data["titulo"] = text.strip()
        state.update({"step": "artista", "data": data})
        sheets.set_conv_state(chat_id, state)
        telegram_client.send_message(chat_id, "¿Quién la canta?")

    elif step == "artista":
        data["artista"] = text.strip()
        state.update({"step": "dedicatoria", "data": data})
        sheets.set_conv_state(chat_id, state)
        telegram_client.send_message(
            chat_id,
            "¿Quieres escribir una dedicatoria?\n_(Por qué le dedicas esta canción... o escribe *no*)_",
        )

    elif step == "dedicatoria":
        data["dedicatoria"] = "" if text.lower().strip() == "no" else text.strip()
        sheets.add_song(
            spotify_id=data.get("spotify_id", ""),
            titulo=data["titulo"],
            artista=data["artista"],
            url=data["url"],
            dedicatoria=data.get("dedicatoria", ""),
        )
        sheets.clear_conv_state(chat_id)
        telegram_client.send_message(
            chat_id,
            f"✅ *{data['titulo']} — {data['artista']}* guardada en Canciones 🎵",
        )


# ------------------------------------------------------------------ #
#  Main update processor                                               #
# ------------------------------------------------------------------ #

def _process_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = str(message["chat"]["id"])
    text = str(message.get("text", "")).strip()

    if not text:
        return

    sheets = SheetsClient()

    # Si hay un flujo conversacional activo y el mensaje no es un comando nuevo,
    # continuar el flujo en lugar de procesar como comando
    if not text.startswith("/"):
        state = sheets.get_conv_state(chat_id)
        if state:
            flow = state.get("flow")
            if flow == "nueva":
                _continue_nueva(chat_id, text, state, sheets)
            elif flow == "cancion":
                _continue_cancion(chat_id, text, state, sheets)
        return

    # Comando nuevo — cancela cualquier flujo previo
    parts = text.lower().split()
    command = parts[0].split("@")[0]

    # Cancelar flujo activo si el usuario manda un comando nuevo
    if command in ("/nueva", "/cancion"):
        pass  # estos arrancan su propio flujo abajo
    else:
        sheets.clear_conv_state(chat_id)

    if command == "/help":
        telegram_client.send_message(chat_id, _HELP_TEXT)

    elif command == "/nueva":
        _start_nueva(chat_id, sheets)

    elif command == "/cancion":
        _start_cancion(chat_id, sheets)

    elif command == "/cita":
        tipo = parts[1] if len(parts) > 1 else None
        if tipo and tipo not in ("finde", "cotidiana"):
            telegram_client.send_message(chat_id, "Uso: /cita, /cita finde, o /cita cotidiana")
            return
        ideas = sheets.get_date_ideas(tipo=tipo)
        if not ideas:
            filtro = f" de tipo *{tipo}*" if tipo else ""
            telegram_client.send_message(chat_id, f"No hay ideas pendientes{filtro} 😅")
            return
        telegram_client.send_message(chat_id, _format_idea(random.choice(ideas)))

    elif command == "/proxima":
        upcoming = sheets.get_upcoming_dates()
        if not upcoming:
            telegram_client.send_message(chat_id, "No hay citas planeadas con fecha aún 📅")
            return
        lines = ["📅 *Próximas citas:*\n"]
        for idea in upcoming[:3]:
            lines.append(_format_idea(idea, show_fecha=True))
        telegram_client.send_message(chat_id, "\n\n".join(lines))

    elif command == "/realizada":
        if len(parts) < 2 or not parts[1].isdigit():
            telegram_client.send_message(chat_id, "Uso: /realizada <número> — ej. /realizada 3")
            return
        numero = int(parts[1])
        found = sheets.mark_date_done(numero)
        if found:
            telegram_client.send_message(chat_id, f"✅ Cita #{numero} marcada como realizada!")
        else:
            telegram_client.send_message(chat_id, f"No encontré la cita #{numero} 🤔")

    else:
        telegram_client.send_message(chat_id, "Comando no reconocido. Escribe /help para ver opciones.")


# ------------------------------------------------------------------ #
#  Vercel handler                                                      #
# ------------------------------------------------------------------ #

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
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
            print(f"[webhook] error: {e}", flush=True)

        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"michicator webhook OK")

    def log_message(self, format, *args):
        pass
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
