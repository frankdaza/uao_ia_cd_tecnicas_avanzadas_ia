"""Fixtures de persistencia TAAM (SQLite in-memory)."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.persistencia.modelos import Base


def _preparar_metadata_sqlite() -> None:
    """Quita defaults solo-Postgres para que ``create_all`` funcione en SQLite."""
    for tabla in Base.metadata.tables.values():
        for columna in tabla.columns:
            if columna.server_default is not None and "gen_random_uuid" in str(
                columna.server_default.arg
            ):
                columna.server_default = None


@pytest.fixture
async def sesion_sqlite() -> AsyncGenerator[AsyncSession, None]:
    """Sesion async sobre SQLite en memoria con esquema creado via metadata."""
    _preparar_metadata_sqlite()
    motor = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    async with motor.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(motor, class_=AsyncSession, expire_on_commit=False)
    async with factory() as sesion:
        yield sesion

    await motor.dispose()
