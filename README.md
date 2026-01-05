# Spotify Playlist Catalog

Spotify Playlist Catalog is a full‑stack web app built to ingest public Spotify playlists by ID and store songs and associated data in PostgreSQL. Each track includes song name, artist, album, and a best-effort [Genius.com](https://genius.com) link to lyrics generated from the metadata. Search via a FastAPI backend and Streamlit dashboard.

Swagger docs: `https://spotify-playlist-catalog.onrender.com/docs`  
Streamlit app: `https://spotify-playlist-catalog.streamlit.app`  
_(Hosting is not in a production environment so there may be a short delay while the documentation loads)_

***

## Features

- Ingest a public Spotify playlist by ID into PostgreSQL
- Streamlit dashboard for:
  - Ingesting new playlists and browsing them.
  - Viewing and searching all ingested tracks by song, artist, and album name with clickable lyrics links.
- Pydantic‑based settings for typed configuration
- 100% Dockerized backend and PostgreSQL database for local development and reproducible deployments.

***

## Tech stack

- **Backend:** FastAPI, Uvicorn
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **ETL:** Spotify Web API, `requests`, `pandas`
- **Config:** Pydantic
- **Dashboard:** Streamlit
- **Containerization:** Docker
- **Hosting:** Render, Streamlit Community Cloud for the dashboard

***

## Architecture

- **Package layout:**
  - `app/core` – configuration and logging 
  - `app/db` – SQLAlchemy models, base, and session management
  - `app/etl` – Spotify client and ETL pipeline
    - `spotify_client.py` for OAuth and playlist retrieval
    - `pipeline.py` to extract playlists, transform with pandas, and load into Postgres.
  - `app/api` – route handlers and dependencies
    - `routes_playlists.py` – ingest and list playlists
    - `routes_tracks.py` – search across ingested tracks.
    - `deps.py` – DB session dependency
  - `app/utils` – `genius.py` to build best‑effort Genius lyrics URLs from artist and track names
  - `dashboard` – `app.py` Streamlit UI that calls the backend and renders playlists, tracks, and lyrics links

## Local Docker development

### 1. Clone & configure

```bash
git clone https://github.com/your-username/spotify-playlist-catalog.git
cd spotify-playlist-catalog

cp .env.example .env
# Edit .env as needed
```

### 2. Build & run backend + Postgres

```bash
docker-compose up --build
# API:  http://localhost:8000
# Docs: http://localhost:8000/docs
```

To stop:

```bash
docker-compose down
```

To stop and reset DB:

```bash
docker-compose down -v
```

### 3. Run the Streamlit dashboard

```bash
cd dashboard
streamlit run app.py
# Dashboard: http://localhost:8501
```

***

## Developer workflow

### 1. Health check

```bash
curl http://localhost:8000/health
```

Expected:

```json
{"status":"ok"}
```

### 2. Ingest a playlist

```bash
curl -X POST "http://localhost:8000/playlists/ingest" \
  -H "Content-Type: application/json" \
  -d '{"playlist_id_or_url": "37i9dQZF1DXcBWIGoYBM5M"}'
```

Expected:

```json
{"playlist_id": 1, "name": "Today’s Top Hits", "track_count": 50}
```

### 3. List playlists

```bash
curl "http://localhost:8000/playlists/"
```

### 4. View tracks for a playlist

```bash
curl "http://localhost:8000/playlists/1/tracks"
```

### 5. Search tracks

```bash
curl "http://localhost:8000/tracks/search?q=Weeknd"
```
