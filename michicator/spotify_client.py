"""
Spotify client — fetches all tracks from a playlist.
Used by sync_playlist.py to populate the Google Sheet.

Authentication: uses OAuth (refresh token) so it works with any playlist
owned by the authenticated user, including public playlists.
Run scripts/get_spotify_token.py once to get the refresh token.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth

_SCOPE = "playlist-read-private playlist-read-collaborative"


def get_client() -> spotipy.Spotify:
    auth_manager = SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=os.environ.get("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback"),
        scope=_SCOPE,
        open_browser=False,
    )

    refresh_token = os.environ.get("SPOTIFY_REFRESH_TOKEN")
    if refresh_token:
        token_info = auth_manager.refresh_access_token(refresh_token)
        return spotipy.Spotify(auth=token_info["access_token"])

    # Fallback: interactive login (only for local setup)
    return spotipy.Spotify(auth_manager=auth_manager)


def get_playlist_tracks(playlist_id: str) -> list[dict]:
    """
    Returns all tracks from a playlist as a list of dicts:
    { spotify_id, titulo, artista, url }
    """
    sp = get_client()
    tracks = []
    offset = 0
    limit = 100

    while True:
        result = sp.playlist_items(
            playlist_id,
            offset=offset,
            limit=limit,
            fields="items(track(id,name,artists,external_urls)),next",
            additional_types=("track",),
        )

        for item in result["items"]:
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

        if result.get("next") is None:
            break
        offset += limit

    return tracks
