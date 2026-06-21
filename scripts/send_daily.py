"""
send_daily.py — punto de entrada principal.

Cómo usar:
  RECIPIENT_OVERRIDE=test python scripts/send_daily.py    # te manda a ti
  RECIPIENT_OVERRIDE=main python scripts/send_daily.py    # manda a ella
"""

import os
import sys

# Permite ejecutar desde la raíz del proyecto
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from michicator.sheets_client import SheetsClient
from michicator import telegram_client
from michicator.message_formatter import format_message


def main() -> None:
    recipient_mode = os.getenv("RECIPIENT_OVERRIDE", "test")
    sheets = SheetsClient()
    config = sheets.get_config()

    # Verificar si el bot está activo
    if config.get("activo", "true").lower() != "true":
        print("ℹ michicator está pausado (activo=false en Config).")
        return

    # Elegir destinatario
    if recipient_mode == "test":
        telegram_id = config["test_telegram_id"]
        print(f" Modo prueba — enviando a ti (ID: {telegram_id})")
    else:
        telegram_id = config["recipient_telegram_id"]
        print(f" Modo principal — enviando a ella (ID: {telegram_id})")

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
        song = sheets.get_next_song()
        if song is None:
            print("⚠ No quedan canciones sin enviar en el Sheet.")

    if modo in ("phrase", "both"):
        phrase = sheets.get_next_phrase()
        if phrase is None:
            print("⚠ No quedan frases sin enviar en el Sheet.")

    if song is None and phrase is None:
        print(" No hay contenido para enviar. Revisa el Sheet.")
        sys.exit(1)

    # Construir y enviar mensaje
    message = format_message(song=song, phrase=phrase)
    print(f"\n--- Mensaje ---\n{message}\n---\n")

    telegram_client.send_message(chat_id=telegram_id, text=message)
    print(" Mensaje enviado.")

    # Marcar como enviado
    if song:
        sheets.mark_song_sent(song["_row"])
        print(f"   Canción marcada: {song['titulo']} — {song['artista']}")

    if phrase:
        sheets.mark_phrase_sent(phrase["_row"])
        print(f"   Frase marcada: {phrase['frase'][:50]}...")

    # Actualizar estado de alternado
    if config.get("modo", "").strip().lower() == "alternate":
        sheets.update_config("last_mode_sent", modo)


if __name__ == "__main__":
    main()
