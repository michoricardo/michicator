"""
get_spotify_token.py — obtiene el refresh token de Spotify.

Corre esto UNA SOLA VEZ para autenticarte con tu cuenta de Spotify.
El refresh token resultante va al .env y a los Secrets de GitHub.

Uso:
  python scripts/get_spotify_token.py
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from spotipy.oauth2 import SpotifyOAuth

_SCOPE = "playlist-read-private playlist-read-collaborative"


def main() -> None:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")

    if not client_id or not client_secret:
        print("❌ Faltan SPOTIFY_CLIENT_ID o SPOTIFY_CLIENT_SECRET en el .env")
        sys.exit(1)

    print("🎵 michicator — Obtener Spotify Refresh Token")
    print("─" * 50)

    auth = SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=_SCOPE,
        open_browser=False,
    )

    auth_url = auth.get_authorize_url()
    print(f"\n1. Abre esta URL en tu navegador:\n\n   {auth_url}\n")
    print("2. Autoriza la app con tu cuenta de Spotify.")
    print("3. Serás redirigido a localhost:8888 (va a fallar la página — eso es normal).")
    print("4. Copia la URL completa de la barra del navegador y pégala aquí.\n")

    redirected_url = input("URL de redirección: ").strip()

    code = auth.parse_response_code(redirected_url)
    token_info = auth.get_access_token(code)

    refresh_token = token_info["refresh_token"]

    print("\n✅ ¡Listo! Agrega esto a tu .env:\n")
    print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")
    print("\nY también agrégalo como Secret en GitHub Actions con el nombre SPOTIFY_REFRESH_TOKEN")


if __name__ == "__main__":
    main()
