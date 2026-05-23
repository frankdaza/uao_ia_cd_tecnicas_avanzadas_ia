"""Fixtures para pruebas del agente TAAM."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.agentes.contexto import establecer_contexto_runtime, limpiar_contexto_runtime
from src.configuracion import obtener_configuracion
from src.persistencia.modelos import Base
from src.persistencia.motor import crear_motor_async, crear_session_factory
from src.persistencia.repositorios.casos_postoperatorio import RepositorioCasosPostoperatorio
from src.persistencia.repositorios.tipos_procedimiento import RepositorioTiposProcedimiento
from src.persistencia.repositorios.vinculos_telegram import RepositorioVinculosTelegram


@pytest.fixture
async def factory_sqlite():
    """Motor y factory SQLite con esquema TAAM."""
    from sqlalchemy import text

    motor = crear_motor_async("sqlite+aiosqlite:///:memory:")
    for tabla in Base.metadata.tables.values():
        for columna in tabla.columns:
            if columna.server_default is not None and "gen_random_uuid" in str(
                columna.server_default.arg
            ):
                columna.server_default = None
    async with motor.begin() as conn:
        await conn.execute(text("PRAGMA foreign_keys=ON"))
        await conn.run_sync(Base.metadata.create_all)
    factory = crear_session_factory(motor)
    yield factory
    await motor.dispose()


@pytest.fixture
async def caso_vinculado_telegram_123(factory_sqlite: async_sessionmaker[AsyncSession]):
    """Caso activo vinculado a ``telegram:123``."""
    async with factory_sqlite() as sesion:
        repo_t = RepositorioTiposProcedimiento(sesion)
        tipo = await repo_t.crear(codigo="demo-hernia", nombre="Hernioplastia demo")
        repo_c = RepositorioCasosPostoperatorio(sesion)
        caso = await repo_c.crear(
            paciente_doc_id="CC-1",
            paciente_nombre="Paciente Demo",
            tipo_procedimiento_id=tipo.id,
            cirujano_id="DOC-1",
            cirujano_nombre="Dr. Demo",
            fecha_cirugia=date(2026, 5, 1),
            notas_especificas="Evitar esfuerzo 7 dias",
        )
        repo_v = RepositorioVinculosTelegram(sesion)
        await repo_v.crear(
            caso_id=caso.id,
            telegram_chat_id=123,
            vinculado_at=datetime.now(timezone.utc),
        )
        await sesion.commit()
        yield caso, tipo


@pytest.fixture
def contexto_agente_123(factory_sqlite: async_sessionmaker[AsyncSession]):
    establecer_contexto_runtime(
        session_id="telegram:123",
        session_factory=factory_sqlite,
    )
    obtener_configuracion.cache_clear()
    yield
    limpiar_contexto_runtime()
