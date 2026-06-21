"""
Google Sheets client — reads config, canciones, frases; marks items as sent.

Sheet structure expected:
  - Tab "Config":   columns [clave, valor]
  - Tab "Canciones": columns [#, spotify_id, titulo, artista, url, enviada, fecha_envio]
  - Tab "Frases":    columns [#, frase, enviada, fecha_envio]
"""

import json
import os
from datetime import datetime, timezone

import gspread
from google.oauth2.service_account import Credentials


_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
]

_DATE_FMT = "%Y-%m-%d %H:%M UTC"


def _get_client() -> gspread.Client:
    raw = os.environ["GOOGLE_CREDENTIALS_JSON"]
    info = json.loads(raw)
    creds = Credentials.from_service_account_info(info, scopes=_SCOPES)
    return gspread.authorize(creds)


class SheetsClient:
    def __init__(self):
        client = _get_client()
        sheet_id = os.environ["GOOGLE_SHEET_ID"]
        self._spreadsheet = client.open_by_key(sheet_id)

    # ------------------------------------------------------------------ #
    #  Config                                                              #
    # ------------------------------------------------------------------ #

    def get_config(self) -> dict[str, str]:
        ws = self._spreadsheet.worksheet("Config")
        rows = ws.get_all_values()
        return {row[0].strip(): row[1].strip() for row in rows if len(row) >= 2 and row[0]}

    def update_config(self, key: str, value: str) -> None:
        ws = self._spreadsheet.worksheet("Config")
        cell = ws.find(key, in_column=1)
        if cell:
            ws.update_cell(cell.row, 2, value)

    # ------------------------------------------------------------------ #
    #  Canciones                                                           #
    # ------------------------------------------------------------------ #

    def get_all_songs(self) -> list[dict]:
        ws = self._spreadsheet.worksheet("Canciones")
        return ws.get_all_records()

    def get_next_song(self) -> dict | None:
        """Returns the first unsent song, or None if all were sent."""
        ws = self._spreadsheet.worksheet("Canciones")
        records = ws.get_all_records()

        for i, row in enumerate(records, start=2):  # row 1 = header
            enviada = str(row.get("enviada", "")).strip().upper()
            if enviada in ("", "FALSE", "NO", "0"):
                return {**row, "_row": i}

        return None

    def mark_song_sent(self, row: int) -> None:
        ws = self._spreadsheet.worksheet("Canciones")
        now = datetime.now(timezone.utc).strftime(_DATE_FMT)
        ws.update_cell(row, 6, "TRUE")       # col F = enviada
        ws.update_cell(row, 7, now)           # col G = fecha_envio

    def upsert_songs(self, tracks: list[dict]) -> int:
        """
        Writes tracks to the Canciones sheet, skipping duplicates by spotify_id.
        Returns the number of new rows added.
        """
        ws = self._spreadsheet.worksheet("Canciones")
        existing = ws.get_all_records()
        existing_ids = {str(r.get("spotify_id", "")) for r in existing}

        new_tracks = [t for t in tracks if t["spotify_id"] not in existing_ids]
        if not new_tracks:
            return 0

        start_row = len(existing) + 2  # +1 header, +1 next empty
        rows = [
            [
                start_row - 1 + i,           # #
                t["spotify_id"],
                t["titulo"],
                t["artista"],
                t["url"],
                "FALSE",                      # enviada
                "",                           # fecha_envio
            ]
            for i, t in enumerate(new_tracks)
        ]
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        return len(new_tracks)

    # ------------------------------------------------------------------ #
    #  Frases                                                              #
    # ------------------------------------------------------------------ #

    def get_next_phrase(self) -> dict | None:
        """Returns the first unsent phrase, or None if all were sent."""
        ws = self._spreadsheet.worksheet("Frases")
        records = ws.get_all_records()

        for i, row in enumerate(records, start=2):
            enviada = str(row.get("enviada", "")).strip().upper()
            if enviada in ("", "FALSE", "NO", "0"):
                return {**row, "_row": i}

        return None

    def mark_phrase_sent(self, row: int) -> None:
        ws = self._spreadsheet.worksheet("Frases")
        now = datetime.now(timezone.utc).strftime(_DATE_FMT)
        ws.update_cell(row, 3, "TRUE")        # col C = enviada
        ws.update_cell(row, 4, now)           # col D = fecha_envio
