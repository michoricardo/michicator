"""
send_daily.py — punto de entrada principal.

Cómo usar:
  RECIPIENT_OVERRIDE=test python scripts/send_daily.py    # te manda a ti
  RECIPIENT_OVERRIDE=main python scripts/send_daily.py    # manda a ella
"""

import os
import sys
import random
from datetime import date, datetime, timezone

# Permite ejecutar desde la raíz del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from michicator.sheets_client import SheetsClient
from michicator import telegram_client
from michicator.message_formatter import format_message


def _days_together(fecha_inicio_str: str) -> int | None:
    """Calcula los días juntos desde fecha_inicio (formato YYYY-MM-DD)."""
    try:
        inicio = date.fromisoformat(fecha_inicio_str.strip())
        return (date.today() - inicio).days
    except Exception:
        return None


def main() -> None:
    recipient_mode = os.getenv("RECIPIENT_OVERRIDE", "test")
    sheets = SheetsClient()
    config = sheets.get_config()

    # Verificar si el bot está activo
    if config.get("activo", "true").lower() != "true":
        print("ℹ michicator está pausado (activo=false en Config).")
        return

    # Verificar si ya se envió hoy
    today_str = date.today().isoformat()
    if config.get("last_sent_date", "").strip() == today_str:
        print(f"ℹ Mensaje ya enviado hoy ({today_str}). Omitiendo.")
        return

    # Elegir destinatario(s)
    if recipient_mode == "test":
        raw_ids = config["test_telegram_id"]
        telegram_ids = [tid.strip() for tid in raw_ids.split(",") if tid.strip()]
        print(f" Modo prueba — enviando a {len(telegram_ids)} destinatario(s): {telegram_ids}")
    else:
        raw_ids = config["recipient_telegram_id"]
        telegram_ids = [tid.strip() for tid in raw_ids.split(",") if tid.strip()]
        print(f" Modo principal — enviando a {len(telegram_ids)} destinatario(s)")

    # Resolver modo de contenido
    modo = config.get("modo", "song").strip().lower()

    if modo == "alternate":
        last = config.get("last_mode_sent", "phrase").strip().lower()
        modo = "phrase" if last == "song" else "song"
        print(f"   Alternando: último fue '{last}', ahora enviando '{modo}'")

    # Obtener contenido según modo
    song = None
    phrase = None

    if modo in ("song", "both"):
        random_order = config.get("orden_canciones", "secuencial").strip().lower() == "random"
        song = sheets.get_next_song(random_order=random_order)
        if song is None:
            print("⚠ No quedan canciones sin enviar en el Sheet.")

    if modo in ("phrase", "both"):
        phrase = sheets.get_next_phrase()
        if phrase is None:
            print("⚠ No quedan frases sin enviar en el Sheet.")

    if song is None and phrase is None:
        print(" No hay contenido para enviar. Revisa el Sheet.")
        sys.exit(1)

    # Contador de días juntos
    days = None
    fecha_inicio = config.get("fecha_inicio", "").strip()
    if fecha_inicio:
        days = _days_together(fecha_inicio)
        if days is not None:
            print(f"   Llevan {days} días juntos 🧡")

    # Miércoles de garrapata — agregar pregunta si es miércoles
    question = None
    es_miercoles = date.today().weekday() == 2  # 0=lunes, 2=miércoles
    miercoles_activo = config.get("miercoles_garrapata", "true").strip().lower() == "true"

    if es_miercoles and miercoles_activo:
        print("   🐱 ¡Miércoles de garrapata! Buscando pregunta...")
        question = sheets.get_next_question()
        if question is None:
            print("⚠ No quedan preguntas sin enviar en el Sheet.")
        else:
            print(f"   Pregunta: {question.get('pregunta', '')[:50]}...")

    # Construir y enviar mensaje
    raw_header = config.get("mensaje_cabecera", "Para ti, hoy ✨")
    if es_miercoles and miercoles_activo:
        raw_header = config.get("mensaje_cabecera_miercoles", raw_header)
    opciones = [h.strip() for h in raw_header.split("|") if h.strip()]
    header = random.choice(opciones) if opciones else "Para ti, hoy ✨"

    message = format_message(song=song, phrase=phrase, header=header,
                             days_together=days, question=question)
    print(f"\n--- Mensaje ---\n{message}\n---\n")

    for tid in telegram_ids:
        telegram_client.send_message(chat_id=tid, text=message)
    print(f" Mensaje enviado a {len(telegram_ids)} destinatario(s).")

    # Marcar como enviado
    if song:
        sheets.mark_song_sent(song["_row"])
        print(f"   Canción marcada: {song['titulo']} — {song['artista']}")

    if phrase:
        sheets.mark_phrase_sent(phrase["_row"])
        print(f"   Frase marcada: {phrase['frase'][:50]}...")

    if question:
        sheets.mark_question_sent(question["_row"])
        print(f"   Pregunta marcada como enviada.")

    # Registrar fecha de envío
    sheets.update_config("last_sent_date", today_str)
    print(f"   Fecha de envío registrada: {today_str}")

    # Actualizar estado de alternado
    if config.get("modo", "").strip().lower() == "alternate":
        sheets.update_config("last_mode_sent", modo)


if __name__ == "__main__":
    main()
