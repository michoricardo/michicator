"""
sync_playlist.py — importa una playlist de Spotify al Google Sheet.

Cómo usar:
  python scripts/sync_playlist.py

Corre esto una vez para poblar la pestaña "Canciones" en tu Sheet.
Si corres de nuevo, solo agrega canciones nuevas (no duplica).
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv

load_dotenv()

from michicator.spotify_client import get_playlist_tracks
from michicator.sheets_client import SheetsClient


def main() -> None:
    playlist_id = os.environ.get("SPOTIFY_PLAYLIST_ID")
    if not playlist_id:
        print("❌ Falta la variable SPOTIFY_PLAYLIST_ID en tu .env")
        sys.exit(1)

    print(f"🎵 Obteniendo canciones de la playlist: {playlist_id} ...")
    tracks = get_playlist_tracks(playlist_id)
    print(f"   {len(tracks)} canciones encontradas en Spotify.")

    print("📝 Escribiendo en Google Sheets ...")
    sheets = SheetsClient()
    added = sheets.upsert_songs(tracks)

    if added == 0:
        print("✅ El Sheet ya tenía todas las canciones. No se agregó nada.")
    else:
        print(f"✅ {added} canciones nuevas agregadas al Sheet.")

    total = len(sheets.get_all_songs())
    print(f"   Total en Sheet: {total} canciones.")


if __name__ == "__main__":
    main()
