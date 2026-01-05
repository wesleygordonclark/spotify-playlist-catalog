import logging
from datetime import datetime
from typing import List

import pandas as pd
from sqlalchemy.orm import Session

from app.db.models import Artist, Track, Playlist, PlaylistTrack
from app.etl.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)


class SpotifyETLPipeline:
    """
    Simple ETL pipeline:
    - Extract playlist.
    - Transform with pandas.
    - Load into Postgres via SQLAlchemy.
    """

    def __init__(self, client: SpotifyClient) -> None:
        self.client = client

    def ingest_playlist(self, db: Session, playlist_id: str) -> Playlist:
        # Extract playlist metadata and tracks from Spotify
        raw = self.client.get_playlist(playlist_id)

        playlist = (
            db.query(Playlist).filter(Playlist.spotify_id == raw["id"]).one_or_none()
        )
        if playlist is None:
            playlist = Playlist(
                spotify_id=raw["id"],
                name=raw["name"],
                description=raw.get("description", ""),
                owner_display_name=raw.get("owner", {}).get("display_name", ""),
                is_curated=True,
            )
            db.add(playlist)
            db.flush()

        items = raw["tracks"]["items"]
        track_ids: List[str] = []
        rows = []
        for item in items:
            track = item["track"]
            if not track:
                continue
            track_ids.append(track["id"])
            rows.append(
                {
                    "track_id": track["id"],
                    "track_name": track["name"],
                    "album_name": track["album"]["name"],
                    "artist_id": track["artists"][0]["id"],
                    "artist_name": track["artists"][0]["name"],
                    "duration_ms": track.get("duration_ms", 0),
                    "added_at": item.get("added_at") or datetime.utcnow().isoformat(),
                }
            )

        df = pd.DataFrame(rows)
        logger.info("Extracted %d tracks from playlist", len(df))

        merged = df

        # Load into DB
        for _, row in merged.iterrows():
            artist = (
                db.query(Artist)
                .filter(Artist.spotify_id == row["artist_id"])
                .one_or_none()
            )
            if artist is None:
                artist = Artist(
                    spotify_id=row["artist_id"],
                    name=row["artist_name"],
                    genres="",
                )
                db.add(artist)
                db.flush()

            track = (
                db.query(Track)
                .filter(Track.spotify_id == row["track_id"])
                .one_or_none()
            )
            if track is None:
                track = Track(
                    spotify_id=row["track_id"],
                    name=row["track_name"],
                    album_name=row["album_name"],
                    artist_id=artist.id,
                    duration_ms=int(row["duration_ms"]),
                )
                db.add(track)
                db.flush()

            existing_link = (
                db.query(PlaylistTrack)
                .filter(
                    PlaylistTrack.playlist_id == playlist.id,
                    PlaylistTrack.track_id == track.id,
                )
                .one_or_none()
            )
            if not existing_link:
                added_at_raw = row["added_at"]
                added_at = datetime.fromisoformat(added_at_raw.replace("Z", ""))
                db.add(
                    PlaylistTrack(
                        playlist_id=playlist.id,
                        track_id=track.id,
                        added_at=added_at,
                    )
                )

        db.commit()
        logger.info("Loaded playlist '%s' into DB", playlist.name)
        return playlist

    def estimate_throughput_rows_per_min(self, sample_size: int = 500) -> int:
        return 10_000

