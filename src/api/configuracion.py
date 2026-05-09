"""Configuración del backend FastAPI leída desde variables de entorno o `.env`."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Configuracion(BaseSettings):
    """Ajustes del servidor API cargados desde el entorno o `.env`."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    api_port: int = 8000

    # Variables del pipeline (compartidas con el resto del proyecto)
    ollama_base_url: str = "http://localhost:11434"
    modelo_llm_defecto: str = "llama3.1:8b"
    openai_api_key: str | None = None


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Retorna la instancia singleton de la configuración (cacheada)."""
    return Configuracion()
