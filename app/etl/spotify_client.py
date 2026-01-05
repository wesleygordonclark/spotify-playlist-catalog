import base64
import logging
from typing import Dict, Any

import requests
from fastapi import HTTPException

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _normalize_playlist_id(raw: str) -> str:

    raw = raw.strip()
    if "open.spotify.com/playlist/" in raw:
        raw = raw.split("open.spotify.com/playlist/")[1]
    if "?" in raw:
        raw = raw.split("?")[0]
    return raw


class SpotifyClient:

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    API_BASE = "https://api.spotify.com/v1"

    def __init__(self) -> None:
        self._access_token: str | None = None

    def _get_access_token(self) -> str:
        if self._access_token:
            return self._access_token

        client_id = settings.spotify_client_id
        client_secret = settings.spotify_client_secret
        if not client_id or not client_secret:
            raise RuntimeError(
                "Spotify client credentials are not set. "
                "Set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in the environment."
            )

        auth_header = base64.b64encode(
            f"{client_id}:{client_secret}".encode()
        ).decode()

        response = requests.post(
            self.TOKEN_URL,
            data={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {auth_header}"},
            timeout=10,
        )
        if response.status_code != 200:
            logger.error(
                "Failed to obtain Spotify access token: %s", response.text
            )
            raise HTTPException(
                status_code=502,
                detail="Failed to obtain Spotify access token from Spotify API.",
            )

        data = response.json()
        token = data["access_token"]
        self._access_token = token
        logger.info("Obtained new Spotify access token")
        return token

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._get_access_token()}"}

    def get_playlist(self, playlist_id: str) -> Dict[str, Any]:
        playlist_id = _normalize_playlist_id(playlist_id)
        params = {"market": settings.spotify_country_market}
        resp = requests.get(
            f"{self.API_BASE}/playlists/{playlist_id}",
            headers=self._headers(),
            params=params,
            timeout=10,
        )
        if resp.status_code == 404:
            logger.warning(
                "Playlist not found or not accessible: %s (%s)",
                playlist_id,
                resp.text,
            )
            raise HTTPException(
                status_code=404,
                detail=(
                    f"Playlist '{playlist_id}' not found or not accessible via Spotify API."
                ),
            )
        if resp.status_code == 401:
            logger.error("Spotify get_playlist unauthorized: %s", resp.text)
            raise HTTPException(
                status_code=502,
                detail="Unauthorized when calling Spotify playlist API.",
            )
        resp.raise_for_status()
        return resp.json()


