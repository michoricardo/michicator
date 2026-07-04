"""
api/webhook.py — Vercel serverless function.
Telegram calls this endpoint via POST for every incoming message.

Commands handled:
  /cita             → random date idea (any type)
  /cita finde       → weekend idea only
  /cita cotidiana   → weekday idea only
  /lista            → full list of pending date ideas
  /lista finde      → pending weekend ideas only
  /lista cotidiana  → pending weekday ideas only
  /lista historial  → all date ideas including realized ones
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

# NOTE: michicator modules are imported lazily (inside functions) so Vercel
# can resolve the handler class at build time without needing the project root
# in sys.path during the static analysis phase.

def _add_project_root():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if root not in sys.path:
        sys.path.insert(0, root)

def _sheets():
    _add_project_root()
    from michicator.sheets_client import SheetsClient
    return SheetsClient()

def _send(chat_id: str, text: str, markdown: bool = True) -> None:
    import requests
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if markdown:
        payload["parse_mode"] = "Markdown"
    resp = requests.post(url, json=payload, timeout=8)
    if not resp.ok:
        print(f"[_send] Telegram error {resp.status_code}: {resp.text[:200]}", flush=True)
        raise RuntimeError(f"Telegram API error {resp.status_code}: {resp.text[:120]}")


_HELP_TEXT = (
    "*Comandos disponibles:*\n\n"
    "/cita — idea de cita aleatoria\n"
    "/cita finde — solo fines de semana\n"
    "/cita cotidiana — solo entre semana\n"
    "/lista — todas las citas pendientes\n"
    "/lista finde — pendientes de finde\n"
    "/lista cotidiana — pendientes cotidianas\n"
    "/lista historial — todas, incluyendo ya realizadas\n"
    "/proxima — próximas citas planeadas\n"
    "/realizada <#> — marcar cita como hecha \n"
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

    tipo_label = {
        "cotidiana": "[cotidiana]",
        "finde": "[finde]",
        "cotidiana/finde": "[ambas]",
    }.get(tipo, "")
    prefix = tipo_label + " " if tipo_label else ""

    lines = [prefix + "*#" + str(numero) + " - " + detalle + "*"]
    if tipo:
        lines.append(f"_{tipo}_")
    if show_fecha and fecha:
        lines.append(f" {fecha}")
    if referencia:
        lines.append(referencia)

    return "\n".join(lines)


def _extract_spotify_id(url: str) -> str:
    match = re.search(r"spotify\.com/track/([A-Za-z0-9]+)", url)
    return match.group(1) if match else ""


def _cmd_lista(chat_id: str, tipo: str | None, sh, historial: bool = False) -> None:
    if historial:
        ideas = sh.get_all_date_ideas(tipo=tipo)
    else:
        ideas = sh.get_date_ideas(tipo=tipo)
    if not ideas:
        filtro = f" de tipo *{tipo}*" if tipo else ""
        _send(chat_id, f"No hay citas{filtro} \U0001f937")
        return

    if historial:
        pendientes = [i for i in ideas if not i.get("_done")]
        realizadas = [i for i in ideas if i.get("_done")]
        tipo_label = {"finde": "finde", "cotidiana": "cotidiana"}.get(tipo or "", "todas")
        header = f"\U0001f4d6 *Historial de citas \u2014 {tipo_label} ({len(pendientes)} pendientes, {len(realizadas)} realizadas):*"
    else:
        tipo_label = {"finde": "finde", "cotidiana": "cotidiana"}.get(tipo or "", "todas")
        header = f"\U0001f4cb *Citas pendientes \u2014 {tipo_label} ({len(ideas)}):*"

    lines = []
    for idea in ideas:
        numero = idea.get("#", "?")
        detalle = str(idea.get("detalle", "")).strip()
        t = str(idea.get("tipo", "")).strip().lower()
        fecha = str(idea.get("fecha", "")).strip()
        referencia = str(idea.get("referencia", "")).strip()
        done = idea.get("_done", False)
        fecha_realizada = str(idea.get("fecha_realizada", "")).strip()

        # Usar cursiva sin corchetes — Telegram MarkdownV1 interpreta [texto]
        # dentro de _..._ como link malformado y rechaza el mensaje silenciosamente
        t_italic = {"cotidiana": "cotidiana", "finde": "finde", "cotidiana/finde": "ambas"}.get(t, t)
        done_mark = " \u2705" if done else ""
        line = f"*#{numero}* {detalle} _{t_italic}_{done_mark}"
        if fecha:
            line += f"\n   \U0001f4c5 {fecha}"
        if done and fecha_realizada:
            line += f"\n   \u2705 realizada: {fecha_realizada}"
        if referencia:
            line += f"\n   \U0001f517 {referencia}"
        lines.append(line)

    # Respetar el límite de 4096 caracteres de Telegram
    chunk = header
    for line in lines:
        candidate = chunk + "\n\n" + line
        if len(candidate) > 3800:
            _send(chat_id, chunk.rstrip())
            chunk = line
        else:
            chunk = candidate
    if chunk:
        _send(chat_id, chunk.rstrip())


# ------------------------------------------------------------------ #
#  Conversational flows                                                #
# ------------------------------------------------------------------ #

def _start_nueva(chat_id: str, sh) -> None:
    sh.set_conv_state(chat_id, {"flow": "nueva", "step": "detalle", "data": {}})
    _send(chat_id, "*Nueva idea de cita*\n\n¿Que quieren hacer? Describe la idea:")


def _start_cancion(chat_id: str, sh) -> None:
    sh.set_conv_state(chat_id, {"flow": "cancion", "step": "url", "data": {}})
    _send(chat_id, "*Nueva cancion*\n\n¿Cual es el link de Spotify?")


def _continue_nueva(chat_id: str, text: str, state: dict, sh) -> None:
    step = state["step"]
    data = state["data"]

    if step == "detalle":
        data["detalle"] = text.strip()
        state.update({"step": "tipo", "data": data})
        sh.set_conv_state(chat_id, state)
        _send(chat_id,
            "¿Para cuándo es? Responde:\n"
            "*cotidiana* — miércoles o entre semana\n"
            "*finde* — viernes, sábado o domingo\n"
            "*ambas* — cualquier día sirve")

    elif step == "tipo":
        tipo_map = {"cotidiana": "cotidiana", "finde": "finde", "ambas": "cotidiana/finde"}
        tipo = tipo_map.get(text.lower().strip())
        if not tipo:
            _send(chat_id, "Escribe *cotidiana*, *finde* o *ambas*:")
            return
        data["tipo"] = tipo
        state.update({"step": "referencia", "data": data})
        sh.set_conv_state(chat_id, state)
        _send(chat_id, "¿Tienes un link de referencia?\n(Google Maps, TikTok, YouTube... o escribe *no*)")

    elif step == "referencia":
        data["referencia"] = "" if text.lower().strip() == "no" else text.strip()
        sh.add_date_idea(data["detalle"], data["tipo"], data.get("referencia", ""))
        sh.clear_conv_state(chat_id)
        _send(chat_id, "¡Guardado en *Dates con Frida*! ")


def _continue_cancion(chat_id: str, text: str, state: dict, sh) -> None:
    step = state["step"]
    data = state["data"]

    if step == "url":
        url = text.strip()
        data["url"] = url
        data["spotify_id"] = _extract_spotify_id(url)
        state.update({"step": "titulo", "data": data})
        sh.set_conv_state(chat_id, state)
        _send(chat_id, "¿Cómo se llama la canción?")

    elif step == "titulo":
        data["titulo"] = text.strip()
        state.update({"step": "artista", "data": data})
        sh.set_conv_state(chat_id, state)
        _send(chat_id, "¿Quién la canta?")

    elif step == "artista":
        data["artista"] = text.strip()
        state.update({"step": "dedicatoria", "data": data})
        sh.set_conv_state(chat_id, state)
        _send(chat_id, "¿Quieres escribir una dedicatoria?\n_(Por qué le dedicas esta canción... o escribe *no*)_")

    elif step == "dedicatoria":
        data["dedicatoria"] = "" if text.lower().strip() == "no" else text.strip()
        sh.add_song(
            spotify_id=data.get("spotify_id", ""),
            titulo=data["titulo"],
            artista=data["artista"],
            url=data["url"],
            dedicatoria=data.get("dedicatoria", ""),
        )
        sh.clear_conv_state(chat_id)
        _send(chat_id, f"*{data['titulo']} - {data['artista']}* guardada en Canciones")


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

    # /help no necesita Google Sheets
    if text.lower().startswith("/help"):
        _send(chat_id, _HELP_TEXT)
        return

    # Para todo lo demás, inicializar SheetsClient
    try:
        sh = _sheets()
    except KeyError as e:
        print(f"[webhook] SheetsClient init error (KeyError): {e}", flush=True)
        _send(chat_id, f"Error: falta variable {e} en Vercel", markdown=False)
        return
    except Exception as e:
        print(f"[webhook] SheetsClient init error ({type(e).__name__}): {e}", flush=True)
        _send(chat_id, f"Sheet error ({type(e).__name__}): {str(e)[:120]}", markdown=False)
        return

    # Mensajes sin / → continuar flujo conversacional si hay uno activo
    if not text.startswith("/"):
        try:
            state = sh.get_conv_state(chat_id)
        except Exception:
            state = None
        if state:
            flow = state.get("flow")
            try:
                if flow == "nueva":
                    _continue_nueva(chat_id, text, state, sh)
                elif flow == "cancion":
                    _continue_cancion(chat_id, text, state, sh)
            except Exception as e:
                print(f"[webhook] flow error ({type(e).__name__}): {e}", flush=True)
                _send(chat_id, f"Error en flujo: {type(e).__name__}: {str(e)[:150]}")
        return

    # Comandos
    parts = text.lower().split()
    command = parts[0].split("@")[0]

    if command not in ("/nueva", "/cancion"):
        try:
            sh.clear_conv_state(chat_id)
        except Exception:
            pass

    try:
        if command == "/nueva":
            _start_nueva(chat_id, sh)

        elif command == "/cancion":
            _start_cancion(chat_id, sh)

        elif command == "/cita":
            tipo = parts[1] if len(parts) > 1 else None
            if tipo and tipo not in ("finde", "cotidiana"):
                _send(chat_id, "Uso: /cita, /cita finde, o /cita cotidiana")
                return
            ideas = sh.get_date_ideas(tipo=tipo)
            if not ideas:
                filtro = f" de tipo *{tipo}*" if tipo else ""
                _send(chat_id, f"No hay ideas pendientes{filtro} ")
                return
            _send(chat_id, _format_idea(random.choice(ideas)))

        elif command == "/lista":
            sub = parts[1] if len(parts) > 1 else None
            if sub == "historial":
                _cmd_lista(chat_id, None, sh, historial=True)
            elif sub and sub not in ("finde", "cotidiana"):
                _send(chat_id, "Uso: /lista, /lista finde, /lista cotidiana, /lista historial")
            else:
                _cmd_lista(chat_id, sub, sh)

        elif command == "/proxima":
            upcoming = sh.get_upcoming_dates()
            if not upcoming:
                _send(chat_id, "No hay citas planeadas con fecha aún ")
                return
            lines = [" *Próximas citas:*\n"]
            for idea in upcoming[:3]:
                lines.append(_format_idea(idea, show_fecha=True))
            _send(chat_id, "\n\n".join(lines))

        elif command == "/realizada":
            if len(parts) < 2 or not parts[1].isdigit():
                _send(chat_id, "Uso: /realizada <número> — ej. /realizada 3")
                return
            numero = int(parts[1])
            if sh.mark_date_done(numero):
                _send(chat_id, f" Cita #{numero} marcada como realizada!")
            else:
                _send(chat_id, f"No encontré la cita #{numero} ")

        else:
            _send(chat_id, "Comando no reconocido. Escribe /help para ver opciones.")

    except Exception as e:
        print(f"[webhook] command error ({type(e).__name__}): {e}", flush=True)
        _send(chat_id, f"Error en comando {command}: {type(e).__name__}: {str(e)[:120]}", markdown=False)


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
