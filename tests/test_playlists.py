# tests/test_playlists.py
from datetime import datetime, timedelta

from app.db.models import Artist, Track, Playlist, PlaylistTrack
from app.etl.pipeline import SpotifyETLPipeline


class DummySpotifyClient:
    """
    Minimal fake that matches SpotifyClient.get_playlist interface.
    """

    def __init__(self):
        now_iso = datetime.utcnow().isoformat() + "Z"
        self._payload = {
            "id": "fake_playlist_id",
            "name": "Fake Playlist",
            "description": "Test playlist",
            "owner": {"display_name": "Test Owner"},
            "tracks": {
                "items": [
                    {
                        "added_at": now_iso,
                        "track": {
                            "id": "track_1",
                            "name": "Song One",
                            "duration_ms": 180000,
                            "album": {"name": "Album One"},
                            "artists": [
                                {
                                    "id": "artist_1",
                                    "name": "Artist One",
                                }
                            ],
                        },
                    },
                    {
                        "added_at": (datetime.utcnow() - timedelta(days=1)).isoformat()
                        + "Z",
                        "track": {
                            "id": "track_2",
                            "name": "Song Two",
                            "duration_ms": 200000,
                            "album": {"name": "Album Two"},
                            "artists": [
                                {
                                    "id": "artist_2",
                                    "name": "Artist Two",
                                }
                            ],
                        },
                    },
                ]
            },
        }

    def get_playlist(self, playlist_id: str):
        return self._payload


def reset_db(db_session):
    db_session.query(PlaylistTrack).delete()
    db_session.query(Track).delete()
    db_session.query(Artist).delete()
    db_session.query(Playlist).delete()
    db_session.commit()


def test_etl_pipeline_ingests_playlist(db_session):
    reset_db(db_session)

    client = DummySpotifyClient()
    pipeline = SpotifyETLPipeline(client=client)

    playlist = pipeline.ingest_playlist(db=db_session, playlist_id="fake_playlist_id")

    # Playlist created
    assert playlist.id is not None
    assert playlist.spotify_id == "fake_playlist_id"
    assert playlist.name == "Fake Playlist"
    assert playlist.is_curated is True

    # Artists and tracks created
    artists = db_session.query(Artist).all()
    tracks = db_session.query(Track).all()
    playlist_tracks = db_session.query(PlaylistTrack).all()

    assert len(artists) == 2
    assert len(tracks) == 2
    assert len(playlist_tracks) == 2


def test_ingest_playlist_endpoint(client, db_session, monkeypatch):
    reset_db(db_session)

    def fake_init(self):
        # avoid using real env credentials
        pass

    def fake_get_playlist(self, playlist_id: str):
        return DummySpotifyClient().get_playlist(playlist_id)

    from app.etl import spotify_client

    monkeypatch.setattr(spotify_client.SpotifyClient, "__init__", fake_init)
    monkeypatch.setattr(spotify_client.SpotifyClient, "get_playlist", fake_get_playlist)

    resp = client.post("/playlists/ingest", json={"playlist_id": "fake_playlist_id"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["spotify_id"] == "fake_playlist_id"
    assert data["name"] == "Fake Playlist"
    assert data["track_count"] == 2

    resp_list = client.get("/playlists/")
    assert resp_list.status_code == 200
    playlists = resp_list.json()
    assert len(playlists) == 1
    assert playlists[0]["name"] == "Fake Playlist"
    assert playlists[0]["track_count"] == 2


def test_get_playlist_tracks_endpoint(client, db_session):
    reset_db(db_session)

    artist = Artist(spotify_id="artist_1", name="Artist One", genres="")
    db_session.add(artist)
    db_session.flush()

    track = Track(
        spotify_id="track_1",
        name="Song One",
        artist_id=artist.id,
        album_name="Album One",
        duration_ms=180000,
    )
    db_session.add(track)
    db_session.flush()

    playlist = Playlist(
        spotify_id="playlist_1",
        name="Playlist One",
        description="",
        owner_display_name="Owner",
        is_curated=True,
    )
    db_session.add(playlist)
    db_session.flush()

    link = PlaylistTrack(
        playlist_id=playlist.id,
        track_id=track.id,
    )
    db_session.add(link)
    db_session.commit()

    resp = client.get(f"/playlists/{playlist.id}/tracks")
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    item = items[0]
    assert item["name"] == "Song One"
    assert item["artist_name"] == "Artist One"
    assert item["album_name"] == "Album One"
    assert item["duration_ms"] == 180000
    assert item["genius_url"].startswith("https://genius.com/")

