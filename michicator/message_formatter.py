"""
Message formatter — builds the Telegram message.
Style: minimalista y elegante.
"""


def format_message(
    song: dict | None = None,
    phrase: dict | None = None,
) -> str:
    """
    Builds the message string depending on what content is available.

    song dict keys: titulo, artista, url
    phrase dict keys: frase
    """
    parts: list[str] = []

    parts.append("Para ti, hoy ✨")

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
