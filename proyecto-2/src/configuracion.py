"""Configuracion TAAM via variables de entorno (pydantic-settings)."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    """Variables del scaffold; se ampliaran en tareas M3 (agente, Telegram, DB)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
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
    qdrant_url: str = Field(default="http://127.0.0.1:6334", validation_alias="QDRANT_URL")
    openai_api_key: str = Field(default="", validation_alias="OPENAI_API_KEY")
    admin_api_key: str = Field(default="", validation_alias="ADMIN_API_KEY")


@lru_cache
def obtener_configuracion() -> Configuracion:
    return Configuracion()
