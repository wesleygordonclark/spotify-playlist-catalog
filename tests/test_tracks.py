# tests/test_tracks.py
from app.db.models import Artist, Track, PlaylistTrack, Playlist


def reset_db(db_session):
    db_session.query(PlaylistTrack).delete()
    db_session.query(Track).delete()
    db_session.query(Artist).delete()
    db_session.query(Playlist).delete()
    db_session.commit()


def seed_tracks(db_session):
    a1 = Artist(spotify_id="artist_1", name="The Weeknd", genres="")
    a2 = Artist(spotify_id="artist_2", name="Taylor Swift", genres="")
    db_session.add_all([a1, a2])
    db_session.flush()

    t1 = Track(
        spotify_id="track_1",
        name="Blinding Lights",
        artist_id=a1.id,
        album_name="After Hours",
        duration_ms=200000,
    )
    t2 = Track(
        spotify_id="track_2",
        name="Lover",
        artist_id=a2.id,
        album_name="Lover",
        duration_ms=190000,
    )
    db_session.add_all([t1, t2])
    db_session.commit()


def test_search_tracks_by_track_name(client, db_session):
    reset_db(db_session)
    seed_tracks(db_session)

    resp = client.get("/tracks/search", params={"q": "blinding"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["name"] == "Blinding Lights"
    assert item["artist_name"] == "The Weeknd"
    assert item["album_name"] == "After Hours"
    assert item["genius_url"].startswith("https://genius.com/")


def test_search_tracks_by_artist_name(client, db_session):
    reset_db(db_session)
    seed_tracks(db_session)

    resp = client.get("/tracks/search", params={"q": "taylor"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    item = data["items"][0]
    assert item["name"] == "Lover"
    assert item["artist_name"] == "Taylor Swift"


def test_search_tracks_empty_query_returns_all_limited(client, db_session):
    reset_db(db_session)
    seed_tracks(db_session)

    resp = client.get("/tracks/search", params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    names = sorted([t["name"] for t in data["items"]])
    assert names == ["Blinding Lights", "Lover"]


def test_search_tracks_no_results(client, db_session):
    reset_db(db_session)
    seed_tracks(db_session)

    resp = client.get("/tracks/search", params={"q": "nonexistent"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []

