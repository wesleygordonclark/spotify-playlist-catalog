from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Playlist, PlaylistTrack, Track
from app.etl.pipeline import SpotifyETLPipeline
from app.etl.spotify_client import SpotifyClient
from app.schemas.track import TrackBase
from app.utils.genius import build_genius_url
from pydantic import BaseModel


router = APIRouter(prefix="/playlists", tags=["playlists"])


class IngestPlaylistPayload(BaseModel):
    playlist_id: str


@router.post("/ingest")
def ingest_playlist_from_spotify(
    payload: IngestPlaylistPayload,
    db: Session = Depends(get_db),
):
    client = SpotifyClient()
    pipeline = SpotifyETLPipeline(client=client)
    playlist = pipeline.ingest_playlist(db=db, playlist_id=payload.playlist_id)
    track_count = (
        db.query(PlaylistTrack)
        .filter(PlaylistTrack.playlist_id == playlist.id)
        .count()
    )
    return {
        "id": playlist.id,
        "spotify_id": playlist.spotify_id,
        "name": playlist.name,
        "track_count": track_count,
    }


@router.get("/", response_model=list[dict])
def list_playlists(db: Session = Depends(get_db)):
    playlists = db.query(Playlist).all()
    result = []
    for p in playlists:
        track_count = (
            db.query(PlaylistTrack)
            .filter(PlaylistTrack.playlist_id == p.id)
            .count()
        )
        result.append(
            {
                "id": p.id,
                "spotify_id": p.spotify_id,
                "name": p.name,
                "description": p.description,
                "owner_display_name": p.owner_display_name,
                "is_curated": p.is_curated,
                "track_count": track_count,
            }
        )
    return result


@router.get("/{playlist_id}/tracks", response_model=List[TrackBase])
def get_playlist_tracks(playlist_id: int, db: Session = Depends(get_db)) -> List[TrackBase]:
    playlist = db.query(Playlist).filter(Playlist.id == playlist_id).one_or_none()
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    q = (
        db.query(Track)
        .join(PlaylistTrack, PlaylistTrack.track_id == Track.id)
        .filter(PlaylistTrack.playlist_id == playlist_id)
        .order_by(Track.name.asc())
    )

    items: List[TrackBase] = []
    for t in q.all():
        artist_name = t.artist.name if t.artist else ""
        genius_url = build_genius_url(artist_name, t.name)
        items.append(
            TrackBase(
                id=t.id,
                spotify_id=t.spotify_id,
                name=t.name,
                album_name=t.album_name,
                artist_name=artist_name,
                duration_ms=t.duration_ms,
                genius_url=genius_url,
            )
        )
    return items



