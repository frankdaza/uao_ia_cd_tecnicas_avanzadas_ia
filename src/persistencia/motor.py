"""Motor async SQLAlchemy y factoria de sesiones (Modulo 2)."""

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
    """
    Crea el motor async para PostgreSQL (``postgresql+asyncpg://``).

    La conexión real se difiere hasta la primera operación salvo pruebas
    explícitas con ``connect()``.
    """
    return create_async_engine(
        url,
        pool_pre_ping=True,
        echo=False,
    )


def crear_session_factory(
    engine: AsyncEngine,
) -> async_sessionmaker[AsyncSession]:
    """
    Factoria de ``AsyncSession`` con ``expire_on_commit=False`` para poder
    leer atributos del ORM tras ``commit`` dentro de la misma petición HTTP.
    """
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def verificar_conexion_inicial(engine: AsyncEngine) -> None:
    """
    Intenta ``SELECT 1`` para detectar problemas de red o credenciales al arranque.

    No interrumpe el arranque de la aplicación; registra un error en español
    sin volcar la URL ni la contraseña.
    """
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error(
            "No se pudo verificar la conexión inicial a la base de datos (%s). "
            "La aplicación seguirá arrancando; revisa migraciones y variables "
            "de entorno de PostgreSQL.",
            exc.__class__.__name__,
            exc_info=False,
        )


async def cerrar_motor_async(engine: AsyncEngine) -> None:
    """Cierra el pool de conexiones del motor (p. ej. en shutdown de la app)."""
    await engine.dispose()


async def obtener_sesion_db(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia FastAPI: abre una sesión, la entrega al endpoint y hace
    ``commit`` si la petición termina sin excepción; en caso contrario,
    ``rollback``.
    """
    factory: async_sessionmaker[AsyncSession] = request.app.state.session_factory
    async with factory() as sesion:
        try:
            yield sesion
            await sesion.commit()
        except Exception:
            await sesion.rollback()
            raise
