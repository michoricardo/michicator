"""Message formatter — builds the Telegram message."""


def _escape_md(text: str) -> str:
    """Escape Telegram MarkdownV1 special characters in user-provided content."""
    for char in ("_", "*", "`", "["):
        text = text.replace(char, f"\\{char}")
    return text


def format_message(
    song: dict | None = None,
    phrase: dict | None = None,
    header: str = "Para ti, hoy ✨",
    days_together: int | None = None,
    question: dict | None = None,
) -> str:
    parts: list[str] = []

    if header:
        days_str = f"\nLlevamos {days_together} días juntos 🧡" if days_together else ""
        parts.append(f"{header}{days_str}")

    if phrase:
        frase = _escape_md(phrase.get("frase", "").strip())
        if frase:
            parts.append(f'\n"{frase}"')

    if song:
        titulo = _escape_md(song.get("titulo", "").strip())
        artista = _escape_md(song.get("artista", "").strip())
        url = song.get("url", "").strip()
        dedicatoria = _escape_md(song.get("dedicatoria", "").strip())

        song_line = f"🎵 {titulo} — {artista}"
        if url:
            song_line += f"\n{url}"
        if dedicatoria:
            song_line += f"\n\n_{dedicatoria}_"

        parts.append(f"\n{song_line}")

    if question:
        pregunta = _escape_md(question.get("pregunta", "").strip())
        if pregunta:
            parts.append(f"\n🌻 Pregunta de hoy:\n{pregunta}")

    return "\n".join(parts)
