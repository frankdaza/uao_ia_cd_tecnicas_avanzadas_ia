"""Checkpointer Postgres (``AsyncPostgresSaver``) para memoria de hilo TAAM."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

from src.configuracion import Configuracion, obtener_configuracion

logger = logging.getLogger(__name__)


def _es_url_sqlite(url: str) -> bool:
    return url.startswith("sqlite") or "sqlite" in url


def _dsn_postgres_desde_url(url: str) -> str:
    """AsyncPostgresSaver espera DSN psycopg (sin prefijo ``+psycopg``)."""
    if _es_url_sqlite(url):
        raise ValueError("AsyncPostgresSaver no aplica con SQLite.")
    return url.replace("postgresql+psycopg://", "postgresql://", 1)


@asynccontextmanager
async def gestionar_checkpointer_postgres_async(
    url: str,
) -> AsyncIterator[AsyncPostgresSaver]:
    """
    Abre ``AsyncPostgresSaver`` para rutas async del grafo (``ainvoke``, ``aupdate_state``).

    Uso en lifespan FastAPI, semilla demo y tests de integracion Postgres.
    """
    dsn = _dsn_postgres_desde_url(url)
    async with AsyncPostgresSaver.from_conn_string(dsn) as saver:
        await saver.setup()
        logger.info("Checkpointer AsyncPostgresSaver TAAM inicializado.")
        yield saver


def crear_checkpointer_para_url(url: str, cfg: Configuracion | None = None) -> BaseCheckpointSaver:
    """
    ``MemorySaver`` para tests SQLite.

    En Postgres use ``gestionar_checkpointer_postgres_async`` en un bloque ``async with``.
    """
    if _es_url_sqlite(url):
        return MemorySaver()
    raise RuntimeError(
        "Para Postgres use gestionar_checkpointer_postgres_async() en un bloque async with; "
        "crear_checkpointer_para_url solo aplica con SQLite."
    )
