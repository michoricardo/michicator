"""Message formatter — builds the Telegram message."""


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
        frase = phrase.get("frase", "").strip()
        if frase:
            parts.append(f'\n"{frase}"')

    if song:
        titulo = song.get("titulo", "").strip()
        artista = song.get("artista", "").strip()
        url = song.get("url", "").strip()
        dedicatoria = song.get("dedicatoria", "").strip()

        song_line = f"🎵 {titulo} — {artista}"
        if url:
            song_line += f"\n{url}"
        if dedicatoria:
            song_line += f"\n\n_{dedicatoria}_"

        parts.append(f"\n{song_line}")

    if question:
        pregunta = question.get("pregunta", "").strip()
        if pregunta:
            parts.append(f"\n🌻 Pregunta de hoy:\n{pregunta}")

    return "\n".join(parts)
