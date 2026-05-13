"""
Entrypoint del backend FastAPI para el sistema Q&A Valle del Lili.

Inicialización:
    uv run uvicorn src.api.main:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from psycopg_pool import ConnectionPool

from src.agentes.memoria.historial import inicializar_esquema_memoria_chat
from src.api.configuracion import obtener_configuracion
from src.api.factoria_grafo_agente import construir_grafo_agente_produccion_o_none
from src.api.middleware_request_id import registrar_request_response
from src.api.routers import agente, salud, sesiones
from src.persistencia.motor import (
    cerrar_motor_async,
    crear_motor_async,
    crear_session_factory,
    verificar_conexion_inicial,
)

logger = logging.getLogger(__name__)

_FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Inicializa el motor async de PostgreSQL (M2) y el grafo del agente conversacional.

    En recarga de Uvicorn (--reload) cada proceso hijo crea y dispone su propio
    motor; no se comparten pools entre procesos.
    """
    cfg = obtener_configuracion()
    logger.info(
        "Modulo vectorial: embeddings=%s modelo=%s coleccion_qdrant=%s "
        "distancia=%s dims=%s",
        cfg.embedding_provider,
        cfg.embedding_model,
        cfg.qdrant_collection,
        cfg.qdrant_distance,
        cfg.embedding_dims,
    )
    app.state.grafo_agente = construir_grafo_agente_produccion_o_none(cfg)

    pool_pg = ConnectionPool(
        conninfo=cfg.url_base_datos_sync(),
        min_size=1,
        max_size=10,
        open=True,
        timeout=60.0,
    )
    app.state.psycopg_pool = pool_pg

    motor_db = crear_motor_async(cfg.url_base_datos_async())
    app.state.engine_db = motor_db
    app.state.session_factory = crear_session_factory(motor_db)
    await verificar_conexion_inicial(motor_db)

    try:
        await asyncio.to_thread(
            inicializar_esquema_memoria_chat,
            cfg.url_base_datos_sync(),
        )
    except Exception as exc:
        logger.error(
            "No se pudo inicializar el esquema de memoria conversacional (%s). "
            "El chat persistente puede fallar hasta que PostgreSQL este disponible.",
            exc.__class__.__name__,
            exc_info=False,
        )

    yield

    await asyncio.to_thread(pool_pg.close)
    await cerrar_motor_async(motor_db)


def crear_app() -> FastAPI:
    """Fabrica la aplicación FastAPI con CORS y routers montados."""
    cfg = obtener_configuracion()

    app = FastAPI(
        title="Fundación Valle del Lili — API (agente M2)",
        description=(
            "Backend HTTP con FastAPI + SSE: sesiones, agente conversacional "
            "(LangGraph + Postgres + Qdrant)."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.allowed_origins,
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.middleware("http")(registrar_request_response)

    app.include_router(salud.router, prefix="/api")
    app.include_router(sesiones.router, prefix="/api")
    app.include_router(agente.router, prefix="/api")

    # Servir el frontend React como estáticos en producción
    if _FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=_FRONTEND_DIST, html=True), name="frontend")

    return app


app = crear_app()
