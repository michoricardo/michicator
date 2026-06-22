"""
import_csv.py — importa canciones desde un CSV exportado por Exportify.

Uso:
  python scripts/import_csv.py ruta/al/archivo.csv

Exportify: https://exportify.app
  1. Login con Spotify
  2. Selecciona tu playlist → Export
  3. Pasa el CSV descargado a este script
"""

import csv
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from michicator.sheets_client import SheetsClient


# Columnas que exporta Exportify (inglés y español)
_POSSIBLE_ID_COLS     = ["URI de la canción", "Spotify ID", "Track ID", "spotify_id"]
_POSSIBLE_TITLE_COLS  = ["Nombre de la canción", "Track Name", "Name", "titulo", "Title"]
_POSSIBLE_ARTIST_COLS = ["Nombre(s) del artista", "Artist Name(s)", "Artist Name", "artista", "Artists"]
_POSSIBLE_URL_COLS    = ["URI de la canción", "Spotify URI", "Track URI", "url", "URL"]


def _find_col(headers: list[str], candidates: list[str]) -> str | None:
    for c in candidates:
        if c in headers:
            return c
    return None


def _uri_to_url(uri_or_url: str) -> str:
    """Convierte spotify:track:ID a https://open.spotify.com/track/ID si es necesario."""
    if uri_or_url.startswith("spotify:track:"):
        track_id = uri_or_url.split(":")[-1]
        return f"https://open.spotify.com/track/{track_id}"
    return uri_or_url


def main() -> None:
    if len(sys.argv) < 2:
        print("❌ Uso: python scripts/import_csv.py ruta/al/archivo.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"❌ No se encontró el archivo: {csv_path}")
        sys.exit(1)

    print(f"📄 Leyendo CSV: {csv_path}")

    tracks = []
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []

        id_col     = _find_col(headers, _POSSIBLE_ID_COLS)
        title_col  = _find_col(headers, _POSSIBLE_TITLE_COLS)
        artist_col = _find_col(headers, _POSSIBLE_ARTIST_COLS)
        url_col    = _find_col(headers, _POSSIBLE_URL_COLS)

        if not id_col or not title_col or not artist_col:
            print(f"❌ No se encontraron las columnas esperadas en el CSV.")
            print(f"   Columnas disponibles: {headers}")
            sys.exit(1)

        for row in reader:
            raw_id     = row.get(id_col, "").strip()
            # Soporta tanto URI (spotify:track:ID) como ID directo
            spotify_id = raw_id.split(":")[-1] if raw_id.startswith("spotify:track:") else raw_id
            titulo     = row.get(title_col, "").strip()
            artista    = row.get(artist_col, "").strip().split(",")[0].strip()  # solo el primer artista
            raw_url    = row.get(url_col, "").strip() if url_col else ""
            url        = f"https://open.spotify.com/track/{spotify_id}"

            if not spotify_id or not titulo:
                continue

            tracks.append({
                "spotify_id": spotify_id,
                "titulo":     titulo,
                "artista":    artista,
                "url":        url,
            })

    print(f"   {len(tracks)} canciones encontradas en el CSV.")

    if not tracks:
        print("⚠️  No se encontraron canciones válidas. Revisa el CSV.")
        sys.exit(1)

    print("📝 Escribiendo en Google Sheets...")
    sheets = SheetsClient()
    added = sheets.upsert_songs(tracks)

    if added == 0:
        print("✅ El Sheet ya tenía todas las canciones. No se agregó nada nuevo.")
    else:
        print(f"✅ {added} canciones nuevas agregadas al Sheet.")

    total = len(sheets.get_all_songs())
    print(f"   Total en Sheet: {total} canciones.")


if __name__ == "__main__":
    main()
