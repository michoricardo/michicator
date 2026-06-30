"""
Google Sheets client — reads config, canciones, frases; marks items as sent.

Sheet structure expected:
  - Tab "Config":          columns [clave, valor]
  - Tab "Canciones":       columns [#, spotify_id, titulo, artista, url, enviada, fecha_envio]
  - Tab "Frases":          columns [#, frase, enviada, fecha_envio]
  - Tab "Dates con Frida": columns [#, detalle, tipo, referencia, fecha, realizada, fecha_realizada]
      tipo values: cotidiana | finde | cotidiana/finde
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

    def get_next_song(self, random_order: bool = False) -> dict | None:
        """Returns the next unsent song. If random_order=True, picks one at random."""
        import random
        ws = self._spreadsheet.worksheet("Canciones")
        records = ws.get_all_records()

        unsent = [
            {**row, "_row": i}
            for i, row in enumerate(records, start=2)
            if str(row.get("enviada", "")).strip().upper() in ("", "FALSE", "NO", "0")
        ]

        if not unsent:
            return None

        return random.choice(unsent) if random_order else unsent[0]

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

    # ------------------------------------------------------------------ #
    #  Preguntas                                                           #
    # ------------------------------------------------------------------ #

    def get_next_question(self) -> dict | None:
        """Returns the first unsent question, or None if all were sent."""
        ws = self._spreadsheet.worksheet("Preguntas")
        records = ws.get_all_records()

        for i, row in enumerate(records, start=2):
            enviada = str(row.get("enviada", "")).strip().upper()
            if enviada in ("", "FALSE", "NO", "0"):
                return {**row, "_row": i}

        return None

    def mark_question_sent(self, row: int) -> None:
        ws = self._spreadsheet.worksheet("Preguntas")
        now = datetime.now(timezone.utc).strftime(_DATE_FMT)
        ws.update_cell(row, 3, "TRUE")        # col C = enviada
        ws.update_cell(row, 4, now)           # col D = fecha_envio

    # ------------------------------------------------------------------ #
    #  Dates con Frida                                                     #
    # ------------------------------------------------------------------ #

    def get_date_ideas(self, tipo: str | None = None) -> list[dict]:
        """
        Returns unrealized date ideas from "Dates con Frida".
        tipo: None → all | 'cotidiana' | 'finde'
        Rows with tipo='cotidiana/finde' match both filters.
        """
        ws = self._spreadsheet.worksheet("Dates con Frida")
        records = ws.get_all_records()

        ideas = []
        for i, row in enumerate(records, start=2):
            if str(row.get("realizada", "")).strip().upper() in ("TRUE", "SI", "YES", "1"):
                continue

            if tipo:
                row_tipo = str(row.get("tipo", "")).strip().lower()
                if tipo == "cotidiana" and row_tipo not in ("cotidiana", "cotidiana/finde"):
                    continue
                if tipo == "finde" and row_tipo not in ("finde", "cotidiana/finde"):
                    continue

            ideas.append({**row, "_row": i})

        return ideas

    def get_upcoming_dates(self) -> list[dict]:
        """Returns unrealized date ideas that have a fecha set, sorted by date."""
        ws = self._spreadsheet.worksheet("Dates con Frida")
        records = ws.get_all_records()

        upcoming = []
        for i, row in enumerate(records, start=2):
            if str(row.get("realizada", "")).strip().upper() in ("TRUE", "SI", "YES", "1"):
                continue
            if not str(row.get("fecha", "")).strip():
                continue
            upcoming.append({**row, "_row": i})

        upcoming.sort(key=lambda r: str(r.get("fecha", "")))
        return upcoming

    def mark_date_done(self, numero: int) -> bool:
        """Marks a date idea as realized by its # number. Returns True if found."""
        ws = self._spreadsheet.worksheet("Dates con Frida")
        records = ws.get_all_records()

        for i, row in enumerate(records, start=2):
            if str(row.get("#", "")).strip() == str(numero):
                now = datetime.now(timezone.utc).strftime(_DATE_FMT)
                ws.update_cell(i, 6, "TRUE")  # col F = realizada
                ws.update_cell(i, 7, now)     # col G = fecha_realizada
                return True

        return False

    def add_date_idea(self, detalle: str, tipo: str, referencia: str = "") -> None:
        """Appends a new date idea to 'Dates con Frida'."""
        ws = self._spreadsheet.worksheet("Dates con Frida")
        numero = len(ws.get_all_records()) + 1
        ws.append_row(
            [numero, detalle, tipo, referencia, "", "FALSE", ""],
            value_input_option="USER_ENTERED",
        )

    def add_song(self, spotify_id: str, titulo: str, artista: str,
                 url: str, dedicatoria: str = "") -> None:
        """Appends a new song to 'Canciones'."""
        ws = self._spreadsheet.worksheet("Canciones")
        numero = len(ws.get_all_records()) + 1
        ws.append_row(
            [numero, spotify_id, titulo, artista, url, dedicatoria, "FALSE", ""],
            value_input_option="USER_ENTERED",
        )

    # ------------------------------------------------------------------ #
    #  Conversation state (flujos interactivos del bot)                   #
    # ------------------------------------------------------------------ #

    def get_conv_state(self, chat_id: str) -> dict | None:
        """Returns the active conversation state for a chat_id, or None."""
        config = self.get_config()
        raw = config.get(f"conv_{chat_id}", "").strip()
        if not raw:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return None

    def set_conv_state(self, chat_id: str, state: dict) -> None:
        """Persists conversation state for a chat_id in the Config tab."""
        key = f"conv_{chat_id}"
        ws = self._spreadsheet.worksheet("Config")
        value = json.dumps(state, ensure_ascii=False)
        cell = ws.find(key, in_column=1)
        if cell:
            ws.update_cell(cell.row, 2, value)
        else:
            ws.append_row([key, value])

    def clear_conv_state(self, chat_id: str) -> None:
        """Clears the conversation state for a chat_id."""
        key = f"conv_{chat_id}"
        ws = self._spreadsheet.worksheet("Config")
        cell = ws.find(key, in_column=1)
        if cell:
            ws.update_cell(cell.row, 2, "")
