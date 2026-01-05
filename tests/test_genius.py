# tests/test_genius.py
from app.utils.genius import build_genius_url


def test_build_genius_url_basic():
    url = build_genius_url("Taylor Swift", "Lover")
    assert url == "https://genius.com/taylor-swift-lover-lyrics"


def test_build_genius_url_strips_and_normalizes():
    url = build_genius_url("  The Weeknd  ", "Blinding Lights!!!")
    assert url == "https://genius.com/the-weeknd-blinding-lights-lyrics"


def test_build_genius_url_ampersand():
    url = build_genius_url("Simon & Garfunkel", "Mrs. Robinson")
    assert url == "https://genius.com/simon-and-garfunkel-mrs-robinson-lyrics"


def test_build_genius_url_empty_inputs():
    assert build_genius_url("", "Song") == ""
    assert build_genius_url("Artist", "") == ""
    assert build_genius_url("", "") == ""
