"""
get_spotify_token.py — obtiene el refresh token de Spotify.

Corre esto UNA SOLA VEZ para autenticarte con tu cuenta de Spotify.
El refresh token resultante va al .env y a los Secrets de GitHub.

Uso:
  python scripts/get_spotify_token.py
"""

import os
import sys
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Event

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from spotipy.oauth2 import SpotifyOAuth

_SCOPE = "playlist-read-private playlist-read-collaborative"
_PORT = 8888
_callback_code = None
_done = Event()


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _callback_code
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        _callback_code = params.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"""
            <html><body style="font-family:sans-serif;text-align:center;padding:60px">
            <h2>&#x2705; michicator autorizado</h2>
            <p>Ya puedes cerrar esta ventana y volver a la terminal.</p>
            </body></html>
        """)
        _done.set()

    def log_message(self, *args):
        pass  # silencia los logs del servidor


def main() -> None:
    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")
    redirect_uri = f"http://localhost:{_PORT}/callback"

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
    print(f"\nAbriendo el navegador para autorizar michicator...")
    print(f"\nSi no se abre automáticamente, copia esta URL:\n\n   {auth_url}\n")

    webbrowser.open(auth_url)

    print("⏳ Esperando autorización en el navegador...")
    server = HTTPServer(("localhost", _PORT), _CallbackHandler)
    server.timeout = 120
    while not _done.is_set():
        server.handle_request()

    if not _callback_code:
        print("❌ No se recibió el código de autorización.")
        sys.exit(1)

    token_info = auth.get_access_token(_callback_code)
    refresh_token = token_info["refresh_token"]

    print("\n✅ ¡Autorización exitosa!\n")
    print("Agrega esto a tu .env:\n")
    print(f"SPOTIFY_REFRESH_TOKEN={refresh_token}")
    print("\nY agrégalo como Secret en GitHub Actions con el nombre SPOTIFY_REFRESH_TOKEN")


if __name__ == "__main__":
    main()
