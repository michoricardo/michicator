"""
Spotify client — fetches all tracks from a playlist.
Used by sync_playlist.py to populate the Google Sheet.

Authentication: uses OAuth (refresh token).
Run scripts/get_spotify_token.py once to get the refresh token.
"""

import os
import requests
from spotipy.oauth2 import SpotifyOAuth

_SCOPE = "playlist-read-private playlist-read-collaborative"
_API_BASE = "https://api.spotify.com/v1"


def _get_access_token() -> str:
    """Gets a fresh access token using the refresh token."""
    auth_manager = SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
        scope=_SCOPE,
        open_browser=False,
    )
    refresh_token = os.environ["SPOTIFY_REFRESH_TOKEN"]
    token_info = auth_manager.refresh_access_token(refresh_token)
    return token_info["access_token"]


def get_playlist_tracks(playlist_id: str) -> list[dict]:
    """
    Returns all tracks from a playlist as a list of dicts:
    { spotify_id, titulo, artista, url }
    Uses requests directly to have full control over API parameters.
    """
    access_token = _get_access_token()
    headers = {"Authorization": f"Bearer {access_token}"}

    tracks = []
    url = f"{_API_BASE}/playlists/{playlist_id}/tracks"
    params = {
        "limit": 100,
        "offset": 0,
        "fields": "items(track(id,name,artists,external_urls)),next",
    }

    while url:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        result = response.json()

        for item in result.get("items", []):
            track = item.get("track")
            if not track or not track.get("id"):
                continue  # skip local files or null entries

            tracks.append(
                {
                    "spotify_id": track["id"],
                    "titulo": track["name"],
                    "artista": track["artists"][0]["name"] if track["artists"] else "Desconocido",
                    "url": track["external_urls"].get("spotify", ""),
                }
            )

        url = result.get("next")
        params = {}  # next URL already includes all params

    return tracks
