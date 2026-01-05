from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import routes_playlists, routes_tracks
from app.core.config import get_settings
from app.core.logging_config import configure_logging
from app.db.base import Base
from app.db.session import engine

configure_logging()
settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Backend API for Spotify Playlist Catalog – ETL and search",
)

if settings.backend_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.backend_cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def on_startup() -> None:
    # In production, create tables if needed.
    # In tests, engine is monkeypatched to the test engine, but tables are
    # already created in conftest, so this is effectively a no-op.
    Base.metadata.create_all(bind=engine)


@app.get("/health", tags=["meta"])
def health():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}


app.include_router(routes_playlists.router)
app.include_router(routes_tracks.router)



