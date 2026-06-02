"""Configuracion TAAM via variables de entorno (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

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
    staff_api_key: str = Field(
        default="",
        validation_alias="STAFF_API_KEY",
        description="Deprecado: sustituido por JWT staff (TASK-105).",
    )
    staff_jwt_secret: str = Field(default="", validation_alias="STAFF_JWT_SECRET")
    staff_jwt_expire_horas: float = Field(
        default=8.0,
        ge=0.25,
        le=72.0,
        validation_alias="STAFF_JWT_EXPIRE_HORAS",
    )
    staff_demo_asistente_password: str = Field(
        default="cambiar-demo-asistente",
        validation_alias="STAFF_DEMO_ASISTENTE_PASSWORD",
    )
    staff_demo_clinico_password: str = Field(
        default="cambiar-demo-clinico",
        validation_alias="STAFF_DEMO_CLINICO_PASSWORD",
    )
    staff_demo_admin_password: str = Field(
        default="cambiar-demo-admin",
        validation_alias="STAFF_DEMO_ADMIN_PASSWORD",
    )
    taam_codigo_emparejamiento_ttl_horas: int = Field(
        default=24,
        ge=1,
        le=168,
        validation_alias="TAAM_CODIGO_EMPAREJAMIENTO_TTL_HORAS",
    )
    taam_codigo_longitud: int = Field(
        default=8,
        ge=6,
        le=8,
        validation_alias="TAAM_CODIGO_LONGITUD",
    )
    taam_pdf_max_mb: int = Field(
        default=10,
        ge=1,
        le=50,
        validation_alias="TAAM_PDF_MAX_MB",
    )
    taam_qdrant_collection: str = Field(
        default="taam_protocolos",
        validation_alias="TAAM_QDRANT_COLLECTION",
    )
    taam_chunk_size: int = Field(default=800, ge=128, le=8192, validation_alias="TAAM_CHUNK_SIZE")
    taam_chunk_overlap: int = Field(
        default=120,
        ge=0,
        le=2048,
        validation_alias="TAAM_CHUNK_OVERLAP",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        validation_alias="EMBEDDING_MODEL",
    )
    agente_modelo: str = Field(
        default="openai:gpt-4o-mini",
        validation_alias="AGENTE_MODELO",
    )
    agente_rag_k: int = Field(default=4, ge=1, le=20, validation_alias="AGENTE_RAG_K")
    chat_timeout_seg: float = Field(
        default=90.0,
        ge=5.0,
        le=300.0,
        validation_alias="CHAT_TIMEOUT_SEG",
        description="Timeout maximo de un turno POST /chat (agente + LLM).",
    )
    taam_sembrar_demo_habilitado: bool = Field(
        default=False,
        validation_alias="TAAM_SEMBRAR_DEMO_HABILITADO",
        description="En Docker entrypoint: ejecuta sembrar_demo_taam tras migraciones.",
    )
    taam_sembrar_demo_con_ingesta: bool = Field(
        default=True,
        validation_alias="TAAM_SEMBRAR_DEMO_CON_INGESTA",
        description="Con semilla demo: indexa COLE-LAP-001 en Qdrant (--con-ingesta).",
    )
    recordatorios_job_habilitado: bool = Field(
        default=True,
        validation_alias="RECORDATORIOS_JOB_HABILITADO",
        description="Activa el job periodico de recordatorios Telegram (UC-MVP-04).",
    )
    recordatorios_job_interval_seg: int = Field(
        default=60,
        ge=5,
        le=3600,
        validation_alias="RECORDATORIOS_JOB_INTERVAL_SEG",
        description="Intervalo del job de recordatorios en segundos.",
    )
    ingesta_reintentos: int = Field(default=3, ge=1, le=10, validation_alias="INGESTA_REINTENTOS")
    ingesta_backoff_max_seg: float = Field(
        default=30.0,
        ge=1.0,
        le=120.0,
        validation_alias="INGESTA_BACKOFF_MAX_SEG",
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
            url = "postgresql+asyncpg://" + url.removeprefix("postgres://")
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
            url = "postgresql+asyncpg://" + url.removeprefix("postgresql://")
        if "sqlite" in url:
            return url
        parsed = urlparse(url)
        sin_query = parsed._replace(query="", fragment="")
        return urlunparse(sin_query)


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
