"""
Spotify client — fetches all tracks from a playlist.
Used by sync_playlist.py to populate the Google Sheet.
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials


def get_client() -> spotipy.Spotify:
    auth_manager = SpotifyClientCredentials(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
    )
    return spotipy.Spotify(auth_manager=auth_manager)


def get_playlist_tracks(playlist_id: str) -> list[dict]:
    """
    Returns all tracks from a playlist as a list of dicts:
    { spotify_id, titulo, artista, url }
    Works with public playlists (no user login needed).
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
