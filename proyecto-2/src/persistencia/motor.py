"""Motor async SQLAlchemy y factoria de sesiones (TAAM)."""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

logger = logging.getLogger(__name__)


def crear_motor_async(url: str) -> AsyncEngine:
    """Crea el motor async (``postgresql+asyncpg://`` o ``sqlite+aiosqlite://`` en tests)."""
    return create_async_engine(url, pool_pre_ping=True, echo=False)


def crear_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """Factoria de ``AsyncSession`` con ``expire_on_commit=False``."""
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def verificar_conexion_inicial(engine: AsyncEngine) -> None:
    """``SELECT 1`` al arranque; no interrumpe el proceso si falla."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "No se pudo verificar la conexion inicial a la base de datos TAAM (%s). "
            "Revisa migraciones Alembic y variables DATABASE_URL / POSTGRES_*.",
            exc.__class__.__name__,
            exc_info=False,
        )


async def cerrar_motor_async(engine: AsyncEngine) -> None:
    """Cierra el pool del motor."""
    await engine.dispose()


async def obtener_sesion_db(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia FastAPI: commit si la peticion termina sin excepcion; rollback si no.
    """
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except Exception:
            await sesion.rollback()
            raise
