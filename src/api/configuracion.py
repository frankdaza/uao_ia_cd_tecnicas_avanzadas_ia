"""Configuración del backend FastAPI leída desde variables de entorno o `.env`."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal, Self
from urllib.parse import quote_plus

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

TipoDistanciaQdrant = Literal["Cosine", "Dot", "Euclid", "Manhattan"]


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

    # --- Modulo 2: PostgreSQL (OLTP + memoria LangChain) ---
    postgres_host: str = "localhost"
    postgres_port: int = Field(default=5432, ge=1, le=65535)
    postgres_db: str = "app"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"
    # Si se define, tiene prioridad sobre el ensamble con POSTGRES_* (debe usar esquema asyncpg).
    database_url: str | None = None

    # --- Modulo 2: Qdrant (vectores densos; ver TASK-52) ---
    qdrant_url: str = Field(
        default="http://localhost:6333",
        description=(
            "URL base del servidor Qdrant (HTTP). Para pruebas unitarias puede "
            "usarse el literal :memory: para un cliente en memoria del proceso."
        ),
    )
    qdrant_api_key: str | None = Field(
        default=None,
        description="Clave API de Qdrant Cloud; opcional en despliegue local.",
    )
    qdrant_collection: str = Field(
        default="corpus_fvl",
        description="Nombre de la coleccion de vectores del corpus indexado.",
    )
    qdrant_distance: TipoDistanciaQdrant = Field(
        default="Cosine",
        description=(
            "Metrica de similitud en Qdrant. Debe coincidir con los valores del "
            "cliente (Cosine, Dot, Euclid, Manhattan)."
        ),
    )

    # --- Modulo 2: embeddings (ingesta + RAG) ---
    embedding_provider: Literal["openai", "huggingface"] = Field(
        default="openai",
        description="Proveedor de embeddings: API OpenAI o modelos locales HuggingFace.",
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description=(
            "Nombre del modelo en el proveedor (p. ej. text-embedding-3-small o "
            "un id de sentence-transformers)."
        ),
    )
    embedding_dims: int = Field(
        default=1536,
        ge=8,
        le=8192,
        description=(
            "Dimension del vector denso; debe coincidir con la coleccion Qdrant y "
            "con el modelo (p. ej. 1536 para text-embedding-3-small por defecto)."
        ),
    )

    # --- Modulo 2: chunking (ingesta) ---
    chunk_size: int = Field(default=512, ge=64, le=8192)
    chunk_overlap: int = Field(default=80, ge=0, le=2048)
    chunk_strategy: str = "sentence"

    # --- Modulo 2: recuperacion densa ---
    rag_top_k: int = Field(default=5, ge=1, le=50)
    rag_score_minimo: float = Field(default=0.25, ge=0.0, le=1.0)

    # --- Modulo 2: memoria conversacional ---
    historial_dias_max: int = Field(default=7, ge=1, le=365)
    historial_turnos_max: int = Field(default=20, ge=1, le=200)

    # --- Modulo 2: FAQ tool ---
    faq_umbral_match: float = Field(default=0.5, ge=0.0, le=1.0)
    # Ruta relativa a la raiz del repo o absoluta; usada por la tool determinista FAQ JSON.
    faq_json_relativo_raiz: str = "data/structured/faqs.json"

    # --- Modulo 2: router LangGraph ---
    router_meta_prompt_path: str = "config/router_meta_prompt.json"
    router_llm_model: str = "gpt-4o-mini"

    # --- Modulo 2: E2E / laboratorio sin OpenAI (tokens e2e70xx en la pregunta; ver scripts/README) ---
    mock_llm: int = Field(
        default=0,
        ge=0,
        le=1,
        description=(
            "1 activa router y compositor deterministicos sin OpenAI (variable de entorno MOCK_LLM)."
        ),
    )

    @model_validator(mode="after")
    def validar_dims_embedding_modelos_openai_fijos(self) -> Self:
        """Modelos OpenAI con dimension de salida fija en la API clasica."""
        if self.embedding_provider != "openai":
            return self
        if self.embedding_model == "text-embedding-ada-002" and self.embedding_dims != 1536:
            raise ValueError(
                "Para text-embedding-ada-002 la dimension de salida es 1536; "
                "ajusta EMBEDDING_DIMS o el modelo."
            )
        return self

    def url_base_datos_async(self) -> str:
        """URL `postgresql+asyncpg://...` lista para `create_async_engine`."""
        if self.database_url and self.database_url.strip():
            return self.database_url.strip()
        usuario = quote_plus(self.postgres_user)
        clave = quote_plus(self.postgres_password)
        return (
            f"postgresql+asyncpg://{usuario}:{clave}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    def url_base_datos_sync(self) -> str:
        """
        URL ``postgresql://...`` para ``psycopg`` (memoria LangChain sync).

        Deriva de ``url_base_datos_async`` sustituyendo el driver ``asyncpg``.
        """
        url = self.url_base_datos_async()
        if "+asyncpg" in url:
            return url.replace("postgresql+asyncpg://", "postgresql://", 1)
        if "+psycopg" in url:
            return url.replace("postgresql+psycopg://", "postgresql://", 1)
        return url


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Retorna la instancia singleton de la configuración (cacheada)."""
    return Configuracion()
