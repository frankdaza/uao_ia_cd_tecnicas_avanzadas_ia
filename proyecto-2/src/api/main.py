"""
Entrypoint del backend FastAPI para TAAM (proyecto-2).

Desarrollo local:
    uv run uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8001
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from src.api.routers import (
    admin_procedimientos,
    auth_staff,
    chat,
    salud,
    staff_casos,
    staff_seguimiento,
    telegram_emparejar,
    telegram_webhook,
)
from src.agentes.checkpointer import gestionar_checkpointer_postgres_async
from src.configuracion import Configuracion, obtener_configuracion
from src.persistencia.modelos import Base
from src.integracion.recordatorios.scheduler import ejecutar_bucle_recordatorios
from src.persistencia.motor import (
    cerrar_motor_async,
    crear_motor_async,
    crear_session_factory,
    verificar_conexion_inicial,
)


def _preparar_metadata_sqlite() -> None:
    """Quita defaults solo-Postgres para ``create_all`` en SQLite (tests)."""
    for tabla in Base.metadata.tables.values():
        for columna in tabla.columns:
            if columna.server_default is not None and "gen_random_uuid" in str(
                columna.server_default.arg
            ):
                columna.server_default = None


async def _arrancar_recursos_app(
    app: FastAPI,
    *,
    cfg: Configuracion,
    url: str,
    motor: AsyncEngine,
) -> tuple[asyncio.Event, asyncio.Task[None] | None]:
    """Motor, sesiones, checkpointer (si SQLite) y job de recordatorios."""
    if "sqlite" in url:
        _preparar_metadata_sqlite()
        async with motor.begin() as conn:
            await conn.execute(text("PRAGMA foreign_keys=ON"))
            await conn.run_sync(Base.metadata.create_all)
        app.state.checkpointer = MemorySaver()

    app.state.engine_db = motor
    app.state.session_factory = crear_session_factory(motor)
    await verificar_conexion_inicial(motor)

    detener_recordatorios = asyncio.Event()
    tarea_recordatorios: asyncio.Task[None] | None = None
    if cfg.recordatorios_job_habilitado:
        tarea_recordatorios = asyncio.create_task(
            ejecutar_bucle_recordatorios(
                app.state.session_factory,
                cfg=cfg,
                detener=detener_recordatorios,
            )
        )
    app.state.tarea_recordatorios = tarea_recordatorios
    return detener_recordatorios, tarea_recordatorios


async def _detener_recursos_app(
    motor: AsyncEngine,
    detener_recordatorios: asyncio.Event,
    tarea_recordatorios: asyncio.Task[None] | None,
) -> None:
    detener_recordatorios.set()
    if tarea_recordatorios is not None:
        tarea_recordatorios.cancel()
        try:
            await tarea_recordatorios
        except asyncio.CancelledError:
            pass
    await cerrar_motor_async(motor)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Motor async de BD, checkpointer y factoria de sesiones."""
    cfg = obtener_configuracion()
    url = app.state.url_bd_override or cfg.url_base_datos_async()
    motor = crear_motor_async(url)

    if "sqlite" in url:
        detener, tarea = await _arrancar_recursos_app(app, cfg=cfg, url=url, motor=motor)
        try:
            yield
        finally:
            await _detener_recursos_app(motor, detener, tarea)
        return

    async with gestionar_checkpointer_postgres_async(cfg.url_base_datos_sync()) as checkpointer:
        app.state.checkpointer = checkpointer
        detener, tarea = await _arrancar_recursos_app(app, cfg=cfg, url=url, motor=motor)
        try:
            yield
        finally:
            await _detener_recursos_app(motor, detener, tarea)


def crear_app(*, url_bd: str | None = None) -> FastAPI:
    """Fabrica la aplicacion (``url_bd`` opcional para tests SQLite)."""
    cfg = obtener_configuracion()
    app = FastAPI(
        title="TAAM API",
        description="Bot posoperatorio — Modulo 3",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.state.url_bd_override = url_bd

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(salud.router, prefix="/api")
    app.include_router(auth_staff.router, prefix="/api")
    app.include_router(admin_procedimientos.router, prefix="/api")
    app.include_router(staff_casos.router, prefix="/api")
    app.include_router(staff_seguimiento.router, prefix="/api")
    app.include_router(telegram_emparejar.router, prefix="/api")
    app.include_router(telegram_webhook.router, prefix="/api")
    app.include_router(chat.router)
    return app


app = crear_app()
