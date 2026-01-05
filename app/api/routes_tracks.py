from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.db.models import Track, Artist
from app.schemas.track import TrackBase, TrackSearchResponse
from app.utils.genius import build_genius_url

router = APIRouter(prefix="/tracks", tags=["tracks"])


@router.get("/search", response_model=TrackSearchResponse)
def search_tracks(
    q: Optional[str] = Query(None, description="Free-text search term"),
    limit: int = 50,
    db: Session = Depends(get_db),
) -> TrackSearchResponse:
    query = db.query(Track).join(Artist)
    if q:
        like_pattern = f"%{q.lower()}%"
        query = query.filter(
            Track.name.ilike(like_pattern) | Artist.name.ilike(like_pattern)
        )
    # No popularity; just sort by track name for deterministic ordering
    query = query.order_by(Track.name.asc()).limit(limit)

    items: List[TrackBase] = []
    for t in query.all():
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
    return TrackSearchResponse(total=len(items), items=items)

