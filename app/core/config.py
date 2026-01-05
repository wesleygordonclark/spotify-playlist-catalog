from functools import lru_cache
from typing import List

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field("Spotify Playlist Catalog", alias="APP_NAME")
    app_env: str = Field("local", alias="APP_ENV")

    backend_cors_origins: List[AnyHttpUrl] = Field(
        default_factory=list,
        alias="BACKEND_CORS_ORIGINS",
    )

    postgres_host: str = Field("localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(5432, alias="POSTGRES_PORT")
    postgres_db: str = Field("spotify_catalog", alias="POSTGRES_DB")
    postgres_user: str = Field("task_user", alias="POSTGRES_USER")
    postgres_password: str = Field("task_password", alias="POSTGRES_PASSWORD")

    spotify_client_id: str = Field("", alias="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field("", alias="SPOTIFY_CLIENT_SECRET")
    spotify_country_market: str = Field("US", alias="SPOTIFY_COUNTRY_MARKET")

    # Used only by the Streamlit dashboard; harmless in backend
    streamlit_backend_url: AnyHttpUrl | None = Field(
        default=None,
        alias="STREAMLIT_BACKEND_URL",
    )

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def database_url(self) -> str:
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()



