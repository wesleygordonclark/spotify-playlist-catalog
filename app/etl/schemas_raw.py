from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class RawArtist(BaseModel):
    id: str
    name: str
    genres: Optional[List[str]] = []


class RawTrack(BaseModel):
    id: str
    name: str
    artists: List[RawArtist]
    duration_ms: int
    album: Dict[str, Any]


class RawPlaylistTrack(BaseModel):
    added_at: Optional[str]
    track: RawTrack


class RawPlaylist(BaseModel):
    id: str
    name: str
    description: str
    owner: Dict[str, Any]
    tracks: Dict[str, Any]

