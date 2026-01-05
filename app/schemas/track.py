from pydantic import BaseModel


class TrackBase(BaseModel):
    id: int
    spotify_id: str
    name: str
    album_name: str
    artist_name: str
    duration_ms: int
    genius_url: str

    class Config:
        from_attributes = True


class TrackSearchResponse(BaseModel):
    total: int
    items: list[TrackBase]

