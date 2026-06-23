"""Message formatter — builds the Telegram message."""


def format_message(
    song: dict | None = None,
    phrase: dict | None = None,
    header: str = "Para ti, hoy ✨",
) -> str:
    parts: list[str] = []

    if header:
        parts.append(header)

    if phrase:
        frase = phrase.get("frase", "").strip()
        if frase:
            parts.append(f'\n"{frase}"')

    if song:
        titulo = song.get("titulo", "").strip()
        artista = song.get("artista", "").strip()
        url = song.get("url", "").strip()

        song_line = f"🎵 {titulo} — {artista}"
        if url:
            song_line += f"\n{url}"

        parts.append(f"\n{song_line}")

    return "\n".join(parts)
