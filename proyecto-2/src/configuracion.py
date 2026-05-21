"""Configuracion TAAM via variables de entorno (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

_RUTA_ENV = Path(__file__).resolve().parent.parent / ".env"


class Configuracion(BaseSettings):
    """Variables de entorno del backend TAAM."""

    model_config = SettingsConfigDict(
        env_file=_RUTA_ENV,
        env_file_encoding="utf-8",
        extra="ignore",
        env_ignore_empty=True,
    )

    allowed_origins: list[str] = Field(
        default=[
            "http://localhost:5174",
            "http://127.0.0.1:5174",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
        ],
        validation_alias="ALLOWED_ORIGINS",
    )

    telegram_bot_token: str = Field(default="", validation_alias="TELEGRAM_BOT_TOKEN")
    telegram_webhook_secret: str = Field(
        default="", validation_alias="TELEGRAM_WEBHOOK_SECRET"
    )
    database_url: str = Field(default="", validation_alias="DATABASE_URL")

    postgres_host: str = Field(default="localhost", validation_alias="POSTGRES_HOST")
    postgres_port: int = Field(default=15433, ge=1, le=65535, validation_alias="POSTGRES_PORT")
    postgres_db: str = Field(default="taam", validation_alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", validation_alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", validation_alias="POSTGRES_PASSWORD")

    qdrant_url: str = Field(default="http://127.0.0.1:6334", validation_alias="QDRANT_URL")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    admin_api_key: str = Field(default="", validation_alias="ADMIN_API_KEY")
    taam_pdf_max_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        validation_alias="TAAM_PDF_MAX_MB",
    )

    def url_base_datos_async(self) -> str:
        """
        URL lista para ``create_async_engine`` (``postgresql+asyncpg://``).

        Normaliza ``postgres://`` y ``postgresql://`` del compose Docker.
        """
        if self.database_url and self.database_url.strip():
            return self._normalizar_url_async(self.database_url.strip())
        usuario = quote_plus(self.postgres_user)
        clave = quote_plus(self.postgres_password)
        return (
            f"postgresql+asyncpg://{usuario}:{clave}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def url_base_datos_sync(self) -> str:
        """URL ``postgresql+psycopg://`` para Alembic y herramientas sync."""
        url = self.url_base_datos_async()
        if url.startswith("postgresql+asyncpg://"):
            return "postgresql+psycopg://" + url.removeprefix("postgresql+asyncpg://")
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url.removeprefix("postgresql://")
        return url

    @staticmethod
    def _normalizar_url_async(url: str) -> str:
        if url.startswith("postgres://"):
            return "postgresql+asyncpg://" + url.removeprefix("postgres://")
        if url.startswith("postgresql://") and "+asyncpg" not in url:
            return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
        return url


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
