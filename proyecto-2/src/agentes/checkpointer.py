"""Checkpointer ``PostgresSaver`` para memoria de hilo TAAM."""

from __future__ import annotations

import logging
from functools import lru_cache

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.postgres import PostgresSaver

from src.configuracion import Configuracion, obtener_configuracion

logger = logging.getLogger(__name__)


def _es_url_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


@lru_cache
def crear_checkpointer_postgres(cfg: Configuracion | None = None) -> PostgresSaver:
    """
    ``PostgresSaver`` sobre la BD TAAM (tablas propias del checkpointer).

    Requiere URL sync ``postgresql+psycopg://`` o ``postgresql://``.
    """
    conf = cfg or obtener_configuracion()
    url = conf.url_base_datos_sync()
    if _es_url_sqlite(url):
        raise ValueError("PostgresSaver no aplica con SQLite; use crear_checkpointer_para_url.")
    # PostgresSaver espera DSN psycopg (sin prefijo +psycopg en algunas versiones).
    dsn = url.replace("postgresql+psycopg://", "postgresql://", 1)
    saver = PostgresSaver.from_conn_string(dsn)
    saver.setup()
    return saver


def crear_checkpointer_para_url(url: str, cfg: Configuracion | None = None) -> BaseCheckpointSaver:
    """Postgres en produccion; ``MemorySaver`` en tests SQLite."""
    if _es_url_sqlite(url):
        return MemorySaver()
    return crear_checkpointer_postgres(cfg)


def inicializar_checkpointer_si_aplica(url: str, cfg: Configuracion | None = None) -> None:
    """Ejecuta ``setup()`` en arranque FastAPI cuando hay Postgres."""
    if _es_url_sqlite(url):
        return
    try:
        crear_checkpointer_postgres(cfg)
        logger.info("Checkpointer PostgresSaver TAAM inicializado.")
    except Exception as exc:
        logger.warning(
            "No se pudo inicializar PostgresSaver (%s). "
            "El agente no persistira hilos hasta corregir DATABASE_URL.",
            exc.__class__.__name__,
        )
