"""Relationship memory utilities for Frida's preferences, bugglers, and shared notes."""

from __future__ import annotations

from datetime import datetime, timezone


class FridaMemory:
    """Stores Frida's preferences, dislikes, and collected fugglers in Google Sheets."""

    def __init__(self, sheets_client):
        self._sheets = sheets_client

    def _ensure(self, title: str, headers: list[str]):
        return self._sheets._get_or_create_ws(title, headers)

    def add_preference(self, category: str, item: str, liked: bool, note: str = "") -> int:
        ws = self._ensure(
            "Preferencias Frida",
            ["#", "categoria", "item", "valor", "nota", "fecha_registro"],
        )
        numero = len(ws.get_all_records()) + 1
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        valor = "le gusta" if liked else "no le gusta"
        ws.append_row([
            numero,
            category.strip(),
            item.strip(),
            valor,
            note.strip(),
            now,
        ], value_input_option="USER_ENTERED")
        return numero

    def add_favorite(self, category: str, item: str, note: str = "") -> int:
        return self.add_preference(category, item, liked=True, note=note)

    def add_dislike(self, category: str, item: str, note: str = "") -> int:
        return self.add_preference(category, item, liked=False, note=note)

    def get_preferences(self, limit: int = 20, liked: bool | None = None, category: str | None = None):
        ws = self._ensure(
            "Preferencias Frida",
            ["#", "categoria", "item", "valor", "nota", "fecha_registro"],
        )
        rows = ws.get_all_records()
        rows = list(reversed(rows))

        filtered = []
        for row in rows:
            row_category = str(row.get("categoria", "")).strip().lower()
            row_value = str(row.get("valor", "")).strip().lower()
            if category and row_category != category.strip().lower():
                continue
            if liked is not None:
                expected = "le gusta" if liked else "no le gusta"
                if row_value != expected:
                    continue
            filtered.append(row)

        return filtered[:limit]

    def add_fuggler(self, nombre: str, descripcion: str = "", file_id: str = "", foto_url: str = "") -> int:
        ws = self._ensure(
            "Fugglers",
            ["#", "nombre", "descripcion", "file_id", "foto_url", "fecha_registro"],
        )
        numero = len(ws.get_all_records()) + 1
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        ws.append_row([
            numero,
            nombre.strip(),
            descripcion.strip(),
            file_id.strip(),
            foto_url.strip(),
            now,
        ], value_input_option="USER_ENTERED")
        return numero

    def attach_fuggler_photo(self, nombre: str, file_id: str, descripcion: str = "") -> dict | None:
        ws = self._ensure(
            "Fugglers",
            ["#", "nombre", "descripcion", "file_id", "foto_url", "fecha_registro"],
        )
        for i, row in enumerate(ws.get_all_records(), start=2):
            if str(row.get("nombre", "")).strip().lower() == nombre.strip().lower():
                if file_id:
                    ws.update_cell(i, 4, file_id)
                if descripcion:
                    ws.update_cell(i, 3, descripcion)
                return {**row, "_row": i}

        return None

    def get_fugglers(self, limit: int = 20):
        ws = self._ensure(
            "Fugglers",
            ["#", "nombre", "descripcion", "file_id", "foto_url", "fecha_registro"],
        )
        rows = ws.get_all_records()
        rows_with_index = [{**row, "_row": idx + 2} for idx, row in enumerate(rows)]
        rows_with_index.reverse()
        return rows_with_index[:limit]

    def get_fuggler_by_name(self, nombre: str):
        for row in self.get_fugglers(limit=200):
            if str(row.get("nombre", "")).strip().lower() == nombre.strip().lower():
                return row
        return None

    def add_date_idea(self, detalle: str, tipo: str = "cotidiana/finde", referencia: str = ""):
        self._sheets.add_date_idea(detalle, tipo, referencia)
