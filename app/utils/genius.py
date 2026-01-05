import re
from urllib.parse import quote


def _slugify(text: str) -> str:
    """
    Convert text to a Genius-style slug fragment.
    This is a heuristic; it won't be perfect but works well for a demo.
    """
    text = text.strip().lower()
    # Replace & with "and"
    text = text.replace("&", "and")
    # Remove anything that's not a letter, number, or space
    text = re.sub(r"[^a-z0-9\s]", "", text)
    # Collapse whitespace and join with hyphens
    parts = text.split()
    return "-".join(parts)


def build_genius_url(artist_name: str, track_name: str) -> str:
    """
    Build a best-effort Genius lyrics URL for a given artist + track.
    Example: "Taylor Swift" + "Lover" ->
    https://genius.com/taylor-swift-lover-lyrics
    """
    if not artist_name or not track_name:
        return ""
    artist_slug = _slugify(artist_name)
    track_slug = _slugify(track_name)
    if not artist_slug or not track_slug:
        return ""
    slug = f"{artist_slug}-{track_slug}-lyrics"
    return f"https://genius.com/{quote(slug)}"
