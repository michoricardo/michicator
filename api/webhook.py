"""
api/webhook.py — Vercel serverless function.
Telegram calls this endpoint via POST for every incoming message.

Commands handled:
  /cita             → random date idea (any type)
  /cita finde       → weekend idea only
  /cita cotidiana   → weekday idea only
    /citaidea <texto> → quick add a date idea
  /lista            → full list of pending date ideas
  /lista finde      → pending weekend ideas only
  /lista cotidiana  → pending weekday ideas only
  /lista historial  → all date ideas including realized ones
  /proxima          → next planned dates (with fecha set)
  /realizada <#>    → mark date #N as done
    /confio           → save why you trust Frida
    /confio <texto>   → quick save trust note
    /confianza        → show recent trust notes
    /recuerdos        → show recent photo memories
    /recuerdo         → send one random memory photo
    /recuerdo reciente → send latest memory photo
    /recuerdofoto <#> → send memory photo by number
  /nueva            → conversational flow to add a date idea
  /cancion          → conversational flow to add a song
    [photo + caption] → save a photo memory in the sheet
  /help             → command list
"""

import json
import html
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

def _esc(text) -> str:
    """HTML-escape user content for Telegram's HTML parse mode."""
    return html.escape(str(text))

def _send(chat_id: str, text: str, parse_mode: str = "HTML") -> None:
    import requests
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    resp = requests.post(url, json=payload, timeout=8)
    if not resp.ok:
        print(f"[_send] Telegram error {resp.status_code}: {resp.text[:200]}", flush=True)
        raise RuntimeError(f"Telegram API error {resp.status_code}: {resp.text[:120]}")


def _send_photo(chat_id: str, file_id: str, caption: str = "") -> None:
    import requests
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": file_id}
    if caption:
        payload["caption"] = caption
        payload["parse_mode"] = "HTML"
    resp = requests.post(url, json=payload, timeout=8)
    if not resp.ok:
        print(f"[_send_photo] Telegram error {resp.status_code}: {resp.text[:200]}", flush=True)
        raise RuntimeError(f"Telegram API error {resp.status_code}: {resp.text[:120]}")


_HELP_TEXT = (
    "<b>Comandos disponibles:</b>\n\n"
    "/cita — idea de cita aleatoria\n"
    "/cita finde — solo fines de semana\n"
    "/cita cotidiana — solo entre semana\n"
    "/citaidea texto — guardar cita rapido\n"
    "/lista — todas las citas pendientes\n"
    "/lista finde — pendientes de finde\n"
    "/lista cotidiana — pendientes cotidianas\n"
    "/lista historial — todas, incluyendo ya realizadas\n"
    "/proxima — próximas citas planeadas\n"
    "/realizada # — marcar cita como hecha \n"
    "/confio — guardar por que confias en Frida\n"
    "/confio texto — guardar nota de confianza rapido\n"
    "/confianza — ver notas de confianza recientes\n"
    "/recuerdos — ver recuerdos con foto recientes\n"
    "/recuerdo — mandar un recuerdo aleatorio\n"
    "/recuerdo reciente — mandar el mas reciente\n"
    "/recuerdofoto # — mandar foto de un recuerdo\n"
    "/nueva — agregar una idea de cita\n"
    "/cancion — agregar una canción\n"
    "/help — esta ayuda"
)

# ------------------------------------------------------------------ #
#  Helpers                                                             #
# ------------------------------------------------------------------ #

def _format_idea(idea: dict, show_fecha: bool = False) -> str:
    numero = idea.get("#", "?")
    detalle = _esc(idea.get("detalle", ""))
    tipo = str(idea.get("tipo", "")).strip().lower()
    referencia = _esc(idea.get("referencia", ""))
    fecha = _esc(idea.get("fecha", ""))

    tipo_label = {
        "cotidiana": "[cotidiana]",
        "finde": "[finde]",
        "cotidiana/finde": "[ambas]",
    }.get(tipo, "")
    prefix = tipo_label + " " if tipo_label else ""

    lines = [prefix + f"<b>#{numero} - {detalle}</b>"]
    if tipo:
        lines.append(f"<i>{_esc(tipo)}</i>")
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
        filtro = f" de tipo <b>{tipo}</b>" if tipo else ""
        _send(chat_id, f"No hay citas{filtro} \U0001f937")
        return

    if historial:
        pendientes = [i for i in ideas if not i.get("_done")]
        realizadas = [i for i in ideas if i.get("_done")]
        tipo_label = {"finde": "finde", "cotidiana": "cotidiana"}.get(tipo or "", "todas")
        header = f"\U0001f4d6 <b>Historial de citas \u2014 {tipo_label} ({len(pendientes)} pendientes, {len(realizadas)} realizadas):</b>"
    else:
        tipo_label = {"finde": "finde", "cotidiana": "cotidiana"}.get(tipo or "", "todas")
        header = f"\U0001f4cb <b>Citas pendientes \u2014 {tipo_label} ({len(ideas)}):</b>"

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
        line = f"<b>#{numero}</b> {_esc(detalle)} <i>{t_italic}</i>{done_mark}"
        if fecha:
            line += f"\n   \U0001f4c5 {_esc(fecha)}"
        if done and fecha_realizada:
            line += f"\n   \u2705 realizada: {_esc(fecha_realizada)}"
        if referencia:
            line += f"\n   \U0001f517 {_esc(referencia)}"
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


def _cmd_confianza(chat_id: str, sh) -> None:
    notes = sh.get_trust_notes(limit=8)
    if not notes:
        _send(chat_id, "Aun no hay notas de confianza. Usa /confio para guardar una ")
        return

    lines = ["🧡 <b>Por qué confias en Frida:</b>"]
    for n in notes:
        numero = n.get("#", "?")
        motivo = _esc(str(n.get("motivo", "")).strip())
        fecha = _esc(str(n.get("fecha_registro", "")).strip())
        line = f"<b>#{numero}</b> {motivo}"
        if fecha:
            line += f"\n   🗓 {fecha}"
        lines.append(line)

    _send(chat_id, "\n\n".join(lines))


def _cmd_recuerdos(chat_id: str, sh) -> None:
    memories = sh.get_recent_memories(limit=8)
    if not memories:
        _send(chat_id, "Aun no hay recuerdos guardados. Manda una foto con caption y yo la registro ")
        return

    lines = ["📸 <b>Recuerdos recientes:</b>"]
    for m in memories:
        numero = m.get("#", "?")
        caption = _esc(str(m.get("caption", "")).strip()) or "(sin descripcion)"
        fecha = _esc(str(m.get("fecha_registro", "")).strip())
        line = f"<b>#{numero}</b> {caption}"
        if fecha:
            line += f"\n   🗓 {fecha}"
        lines.append(line)

    lines.append("\nTip: usa /recuerdo para uno aleatorio o /recuerdo reciente")
    _send(chat_id, "\n\n".join(lines))


def _memory_caption(memory: dict) -> str:
    numero = _esc(str(memory.get("#", "?")).strip())
    caption = _esc(str(memory.get("caption", "")).strip()) or "(sin descripcion)"
    fecha = _esc(str(memory.get("fecha_registro", "")).strip())
    cap = f"📸 <b>Recuerdo #{numero}</b>\n{caption}"
    if fecha:
        cap += f"\n🗓 {fecha}"
    return cap


def _cmd_recuerdo_random(chat_id: str, sh) -> None:
    memories = sh.get_all_memories()
    if not memories:
        _send(chat_id, "Aun no hay recuerdos guardados. Manda una foto con caption y yo la registro ")
        return
    memory = random.choice(memories)
    file_id = str(memory.get("file_id", "")).strip()
    if not file_id:
        _send(chat_id, "Ese recuerdo no tiene foto utilizable, intenta otro.")
        return
    _send_photo(chat_id, file_id=file_id, caption=_memory_caption(memory))


def _cmd_recuerdo_latest(chat_id: str, sh) -> None:
    memory = sh.get_latest_memory()
    if not memory:
        _send(chat_id, "Aun no hay recuerdos guardados. Manda una foto con caption y yo la registro ")
        return
    file_id = str(memory.get("file_id", "")).strip()
    if not file_id:
        _send(chat_id, "El recuerdo mas reciente no tiene foto utilizable.")
        return
    _send_photo(chat_id, file_id=file_id, caption=_memory_caption(memory))


def _cmd_recuerdo_by_number(chat_id: str, sh, numero: int) -> None:
    memory = sh.get_memory_by_number(numero)
    if not memory:
        _send(chat_id, f"No encontre el recuerdo #{numero}")
        return
    file_id = str(memory.get("file_id", "")).strip()
    if not file_id:
        _send(chat_id, f"El recuerdo #{numero} no tiene foto utilizable")
        return
    _send_photo(chat_id, file_id=file_id, caption=_memory_caption(memory))


# ------------------------------------------------------------------ #
#  Conversational flows                                                #
# ------------------------------------------------------------------ #

def _start_nueva(chat_id: str, sh) -> None:
    sh.set_conv_state(chat_id, {"flow": "nueva", "step": "detalle", "data": {}})
    _send(chat_id, "<b>Nueva idea de cita</b>\n\n¿Que quieren hacer? Describe la idea:")


def _start_cancion(chat_id: str, sh) -> None:
    sh.set_conv_state(chat_id, {"flow": "cancion", "step": "url", "data": {}})
    _send(chat_id, "<b>Nueva cancion</b>\n\n¿Cual es el link de Spotify?")


def _start_confio(chat_id: str, sh) -> None:
    sh.set_conv_state(chat_id, {"flow": "confio", "step": "motivo", "data": {}})
    _send(chat_id, "<b>Confio en Frida</b>\n\nEscribe por que confias en ella hoy:")


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
        _send(chat_id, "¿Quieres escribir una dedicatoria?\n<i>(Por qué le dedicas esta canción... o escribe <b>no</b>)</i>")

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
        _send(chat_id, f"<b>{_esc(data['titulo'])} - {_esc(data['artista'])}</b> guardada en Canciones")


def _continue_confio(chat_id: str, text: str, sh) -> None:
    motivo = text.strip()
    if not motivo:
        _send(chat_id, "Escribe una razon breve de confianza ")
        return
    numero = sh.add_trust_note(motivo)
    sh.clear_conv_state(chat_id)
    _send(chat_id, f"🧡 Nota de confianza guardada como <b>#{numero}</b>")


# ------------------------------------------------------------------ #
#  Main update processor                                               #
# ------------------------------------------------------------------ #

def _process_update(update: dict) -> None:
    message = update.get("message") or update.get("edited_message")
    if not message:
        return

    chat_id = str(message["chat"]["id"])
    text = str(message.get("text", "")).strip()
    caption = str(message.get("caption", "")).strip()
    photos = message.get("photo") or []
    message_id = int(message.get("message_id", 0))

    # /help no necesita Google Sheets
    if text.lower().startswith("/help"):
        _send(chat_id, _HELP_TEXT)
        return

    # Para todo lo demás, inicializar SheetsClient
    try:
        sh = _sheets()
    except KeyError as e:
        print(f"[webhook] SheetsClient init error (KeyError): {e}", flush=True)
        _send(chat_id, f"Error: falta variable {_esc(e)} en Vercel", parse_mode=None)
        return
    except Exception as e:
        print(f"[webhook] SheetsClient init error ({type(e).__name__}): {e}", flush=True)
        _send(chat_id, f"Sheet error ({_esc(type(e).__name__)}): {_esc(str(e)[:120])}", parse_mode=None)
        return

    # Si llega foto, guardarla como recuerdo aunque no tenga comando.
    if photos:
        best = photos[-1]
        file_id = str(best.get("file_id", "")).strip()
        file_unique_id = str(best.get("file_unique_id", "")).strip()
        if file_id:
            idx = sh.add_memory_photo(
                chat_id=chat_id,
                message_id=message_id,
                file_id=file_id,
                file_unique_id=file_unique_id,
                caption=caption,
            )
            _send(chat_id, f"📸 Recuerdo guardado como <b>#{idx}</b>. Usa /recuerdos para verlos.")
        return

    if not text:
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
                elif flow == "confio":
                    _continue_confio(chat_id, text, sh)
            except Exception as e:
                print(f"[webhook] flow error ({type(e).__name__}): {e}", flush=True)
                _send(chat_id, f"Error en flujo: {_esc(type(e).__name__)}: {_esc(str(e)[:150])}")
        return

    # Comandos
    raw_parts = text.split()
    parts = text.lower().split()
    command = parts[0].split("@")[0]

    if command not in ("/nueva", "/cancion", "/confio"):
        try:
            sh.clear_conv_state(chat_id)
        except Exception:
            pass

    try:
        if command == "/nueva":
            _start_nueva(chat_id, sh)

        elif command == "/cancion":
            _start_cancion(chat_id, sh)

        elif command == "/confio":
            if len(raw_parts) > 1:
                motivo = text[len(raw_parts[0]):].strip()
                if not motivo:
                    _send(chat_id, "Uso: /confio o /confio <texto>")
                    return
                idx = sh.add_trust_note(motivo)
                _send(chat_id, f"🧡 Nota de confianza guardada como <b>#{idx}</b>")
            else:
                _start_confio(chat_id, sh)

        elif command == "/confianza":
            _cmd_confianza(chat_id, sh)

        elif command == "/recuerdos":
            _cmd_recuerdos(chat_id, sh)

        elif command == "/recuerdo":
            sub = parts[1] if len(parts) > 1 else ""
            if sub in ("", "azar", "aleatorio"):
                _cmd_recuerdo_random(chat_id, sh)
            elif sub in ("reciente", "ultimo", "último"):
                _cmd_recuerdo_latest(chat_id, sh)
            else:
                _send(chat_id, "Uso: /recuerdo o /recuerdo reciente")

        elif command == "/recuerdofoto":
            if len(parts) < 2 or not parts[1].isdigit():
                _send(chat_id, "Uso: /recuerdofoto # — ej. /recuerdofoto 3")
                return
            _cmd_recuerdo_by_number(chat_id, sh, int(parts[1]))

        elif command == "/cita":
            tipo = parts[1] if len(parts) > 1 else None
            if tipo and tipo not in ("finde", "cotidiana"):
                _send(chat_id, "Uso: /cita, /cita finde, o /cita cotidiana")
                return
            ideas = sh.get_date_ideas(tipo=tipo)
            if not ideas:
                filtro = f" de tipo <b>{tipo}</b>" if tipo else ""
                _send(chat_id, f"No hay ideas pendientes{filtro} ")
                return
            _send(chat_id, _format_idea(random.choice(ideas)))

        elif command == "/citaidea":
            detalle = text[len(raw_parts[0]):].strip() if raw_parts else ""
            if not detalle:
                _send(chat_id, "Uso: /citaidea <idea de cita>")
                return
            sh.add_date_idea(detalle=detalle, tipo="cotidiana/finde", referencia="")
            _send(chat_id, "🗓 Cita guardada rapido en Dates con Frida como tipo ambas")

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
            lines = ["\U0001f4c5 <b>Próximas citas:</b>\n"]
            for idea in upcoming[:3]:
                lines.append(_format_idea(idea, show_fecha=True))
            _send(chat_id, "\n\n".join(lines))

        elif command == "/realizada":
            if len(parts) < 2 or not parts[1].isdigit():
                _send(chat_id, "Uso: /realizada # \u2014 ej. /realizada 3")
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
        _send(chat_id, f"Error en comando {_esc(command)}: {_esc(type(e).__name__)}: {_esc(str(e)[:120])}", parse_mode=None)


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
