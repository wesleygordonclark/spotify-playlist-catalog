import os

import pandas as pd
import requests
import streamlit as st

BACKEND_URL = os.getenv("STREAMLIT_BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Spotify Playlist Catalog", layout="wide")

st.title("Spotify Playlist Catalog")
st.caption("Ingest Spotify playlists, store track metadata, and browse tracks with lyrics links.")


@st.cache_data(ttl=60)
def fetch_playlists():
    resp = requests.get(f"{BACKEND_URL}/playlists/", timeout=10)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=60)
def fetch_playlist_tracks(playlist_id: int):
    # Backend endpoint: /playlists/{playlist_id}/tracks
    resp = requests.get(f"{BACKEND_URL}/playlists/{playlist_id}/tracks", timeout=10)
    resp.raise_for_status()
    return resp.json()


@st.cache_data(ttl=0)
def ingest_playlist(playlist_id: str):
    resp = requests.post(
        f"{BACKEND_URL}/playlists/ingest",
        json={"playlist_id": playlist_id},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


tab_playlists, tab_search = st.tabs(["Playlists", "Search tracks"])

# ----------------- PLAYLISTS -----------------
with tab_playlists:
    st.subheader("Playlists")

    col_left, col_right = st.columns([1, 2])

    # ---------- LEFT: ingest + existing playlists ----------
    with col_left:
        st.markdown("#### Ingest playlist from Spotify")
        st.caption(
            "Paste a public Spotify playlist ID, e.g. from `https://open.spotify.com/playlist/<ID>`."
        )
        playlist_id_input = st.text_input("Playlist ID", value="")
        if st.button("Ingest playlist", type="primary") and playlist_id_input:
            with st.spinner("Ingesting playlist via Spotify Web API..."):
                try:
                    pl = ingest_playlist(playlist_id_input.strip())
                    st.success(f"Ingested playlist: {pl['name']}")
                    # Clear cached playlist list so UI updates immediately
                    fetch_playlists.clear()
                    # Remember this as the most recently ingested playlist
                    st.session_state["last_ingested_playlist_id"] = int(pl["id"])
                except Exception as exc:  # noqa: BLE001
                    st.error(f"Failed to ingest playlist: {exc}")

        st.markdown("#### Existing playlists")
        try:
            playlists = fetch_playlists()
            if playlists:
                pl_df = pd.DataFrame(playlists)
                # Ensure id column is plain Python int (not int64)
                pl_df["id"] = pl_df["id"].astype(int)

                # Default selection: most recently ingested playlist if available
                default_index = 0
                last_ingested_id = st.session_state.get("last_ingested_playlist_id")
                if last_ingested_id is not None:
                    match = pl_df[pl_df["id"] == int(last_ingested_id)]
                    if not match.empty:
                        default_index = int(match.index[0])

                selected_name = st.selectbox(
                    "Select playlist",
                    options=pl_df["name"].tolist(),
                    index=default_index,
                )
                selected = pl_df[pl_df["name"] == selected_name].iloc[0]
                st.session_state["selected_playlist_id"] = int(selected["id"])
                st.write(f"Tracks: {int(selected['track_count'])}")
            else:
                st.info("No playlists ingested yet.")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to load playlists: {exc}")

    # ---------- RIGHT: playlist details (for selected / last ingested) ----------
    with col_right:
        st.markdown("#### Playlist details")
        playlist_id = st.session_state.get("selected_playlist_id") or st.session_state.get(
            "last_ingested_playlist_id"
        )
        if playlist_id:
            try:
                # Look up playlist name from the playlists list
                playlists = fetch_playlists()
                pl_df = pd.DataFrame(playlists)
                pl_df["id"] = pl_df["id"].astype(int)

                row = pl_df[pl_df["id"] == int(playlist_id)]

                if not row.empty:
                    playlist_name = row["name"].iloc[0]
                else:
                    playlist_name = str(playlist_id)

                # All tracks for this playlist from backend
                tracks = fetch_playlist_tracks(int(playlist_id))
                df = pd.DataFrame(tracks)

                if df.empty:
                    st.info("No tracks found for this playlist yet.")
                else:
                    actual_track_count = int(len(df))
                    st.write(
                        f"**{playlist_name}** (ID: {int(playlist_id)}) — {actual_track_count} tracks"
                    )

                    df = df.sort_values("name", ascending=True)
                    st.markdown("Tracks in this playlist")
                    st.dataframe(
                        df[
                            [
                                "name",
                                "genius_url",
                                "artist_name",
                                "album_name",
                            ]
                        ],
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "name": "Song name",
                            "artist_name": "Artist name",
                            "album_name": "Album name",
                            "genius_url": st.column_config.LinkColumn(
                                "Lyrics",
                                help="Open lyrics on Genius.com",
                            ),
                        },
                    )
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed to load playlist details: {exc}")
        else:
            st.info("Ingest a playlist, or select one on the left, to see its tracks.")

# ----------------- SEARCH TRACKS -----------------
with tab_search:
    st.subheader("Search ingested tracks")

    q = st.text_input("Search term (track or artist name)", value="")
    search_clicked = st.button("Search")

    if search_clicked:
        try:
            resp = requests.get(
                f"{BACKEND_URL}/tracks/search",
                params={"q": q, "limit": 100},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            df = pd.DataFrame(data["items"])
            if df.empty:
                st.info("No results.")
            else:
                df = df.sort_values("name", ascending=True)
                st.dataframe(
                    df[
                        [
                            "name",
                            "genius_url",
                            "artist_name",
                            "album_name",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "name": "Song name",
                        "artist_name": "Artist name",
                        "album_name": "Album name",
                        "genius_url": st.column_config.LinkColumn(
                            "Lyrics",
                            help="Open lyrics on Genius.com",
                        ),
                    },
                )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Search failed: {exc}")
