from pydantic import BaseModel


class PlaylistBase(BaseModel):
    id: int
    spotify_id: str | None = None
    name: str
    description: str
    owner_display_name: str
    is_curated: bool

    class Config:
        from_attributes = True


class PlaylistWithCounts(PlaylistBase):
    track_count: int


class PlaylistCreateFromSpotify(BaseModel):
    playlist_id: str
