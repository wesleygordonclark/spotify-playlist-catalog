from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
from app.db.base import Base


class Artist(Base):
    __tablename__ = "artists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    spotify_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, index=True)
    genres: Mapped[str] = mapped_column(String, default="")

    tracks: Mapped[list["Track"]] = relationship("Track", back_populates="artist")


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    spotify_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, index=True)
    artist_id: Mapped[int] = mapped_column(ForeignKey("artists.id"), nullable=False)
    album_name: Mapped[str] = mapped_column(String, default="")
    duration_ms: Mapped[int] = mapped_column(Integer)

    artist: Mapped["Artist"] = relationship("Artist", back_populates="tracks")
    playlist_items: Mapped[list["PlaylistTrack"]] = relationship(
        "PlaylistTrack", back_populates="track"
    )


class Playlist(Base):
    __tablename__ = "playlists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    spotify_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String, index=True)
    description: Mapped[str] = mapped_column(String, default="")
    owner_display_name: Mapped[str] = mapped_column(String, default="")
    is_curated: Mapped[bool] = mapped_column(default=False)

    items: Mapped[list["PlaylistTrack"]] = relationship(
        "PlaylistTrack", back_populates="playlist", cascade="all, delete-orphan"
    )


class PlaylistTrack(Base):
    __tablename__ = "playlist_tracks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    playlist_id: Mapped[int] = mapped_column(ForeignKey("playlists.id"), nullable=False)
    track_id: Mapped[int] = mapped_column(ForeignKey("tracks.id"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    playlist: Mapped["Playlist"] = relationship("Playlist", back_populates="items")
    track: Mapped["Track"] = relationship("Track", back_populates="playlist_items")

    __table_args__ = (UniqueConstraint("playlist_id", "track_id", name="uix_playlist_track"),)
