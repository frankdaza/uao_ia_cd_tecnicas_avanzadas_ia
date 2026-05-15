"""
Integracion: motor async, dependencia ``obtener_sesion_db`` y ``RepositorioUsuarios``.

Activa con ``EJECUTAR_INTEGRACION_POSTGRES=1`` (misma convencion que
``test_migracion_usuarios_postgres``). Aplica migraciones Alembic y usa
``INTEGRATION_POSTGRES_ASYNC_URL`` o ``Configuracion``.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from fastapi import Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.configuracion import obtener_configuracion
from src.persistencia.motor import (
    cerrar_motor_async,
    crear_motor_async,
    crear_session_factory,
    obtener_sesion_db,
)
from src.persistencia.repositorios.usuarios import RepositorioUsuarios


def _url_async_integracion() -> str:
    if os.environ.get("EJECUTAR_INTEGRACION_POSTGRES", "").strip() != "1":
        return ""
    obtener_configuracion.cache_clear()
    url_async = os.environ.get("INTEGRATION_POSTGRES_ASYNC_URL", "").strip()
    if not url_async:
        url_async = obtener_configuracion().url_base_datos_async()
    if not url_async.startswith("postgresql+asyncpg://"):
        return ""
    return url_async


def _aplicar_migraciones_si_postgres(url_async: str) -> None:
    sync_url = (
        make_url(url_async)
        .set(drivername="postgresql+psycopg")
        .render_as_string(hide_password=False)
    )
    raiz = Path(__file__).resolve().parents[2]
    os.environ["ALEMBIC_SYNC_DATABASE_URL"] = sync_url
    alembic_cfg = Config(str(raiz / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(raiz / "alembic"))
    command.upgrade(alembic_cfg, "head")


def _crear_app_prueba(url_async: str) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        motor = crear_motor_async(url_async)
        app.state.engine_db = motor
        app.state.session_factory = crear_session_factory(motor)
        yield
        await cerrar_motor_async(motor)

    app = FastAPI(lifespan=lifespan)

    @app.get("/obtener-o-crear")
    async def ruta_upsert(
        documento: str,
        sesion: AsyncSession = Depends(obtener_sesion_db),
    ) -> dict[str, str | bool]:
        repo = RepositorioUsuarios(sesion)
        usuario, ya_existia = await repo.obtener_o_crear(documento, "Nombre integracion")
        return {
            "id": str(usuario.id),
            "ya_existia": ya_existia,
        }

    @app.post("/last-login/{usuario_id}")
    async def ruta_login(
        usuario_id: str,
        sesion: AsyncSession = Depends(obtener_sesion_db),
    ) -> dict[str, str]:
        repo = RepositorioUsuarios(sesion)
        await repo.actualizar_last_login(UUID(usuario_id))
        return {"ok": "true"}

    return app


@pytest.mark.integration_postgres
@pytest.mark.asyncio
async def test_obtener_sesion_db_y_repositorio_upsert() -> None:
    url_async = _url_async_integracion()
    if not url_async:
        pytest.skip(
            "Define EJECUTAR_INTEGRACION_POSTGRES=1 y una URL async de PostgreSQL."
        )

    try:
        _aplicar_migraciones_si_postgres(url_async)
    except OperationalError as exc:
        pytest.skip(f"Postgres no alcanzable para integracion: {exc}")

    app = _crear_app_prueba(url_async)
    documento = f"doc-int-{uuid4().hex}"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.get(
            "/obtener-o-crear",
            params={"documento": documento},
        )
        assert r1.status_code == 200
        body1 = r1.json()
        assert body1["ya_existia"] is False
        uid = body1["id"]

        r2 = await client.get(
            "/obtener-o-crear",
            params={"documento": documento},
        )
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2["ya_existia"] is True
        assert body2["id"] == uid

        r3 = await client.post(f"/last-login/{uid}")
        assert r3.status_code == 200

    sync_url = (
        make_url(url_async)
        .set(drivername="postgresql+psycopg")
        .render_as_string(hide_password=False)
    )
    engine_sync = create_engine(sync_url)
    try:
        with engine_sync.connect() as conn:
            ultimo = conn.execute(
                text(
                    "SELECT last_login_at FROM usuarios WHERE id = CAST(:id AS uuid)"
                ),
                {"id": uid},
            ).one()
        assert ultimo[0] is not None
        assert getattr(ultimo[0], "tzinfo", None) is not None
    finally:
        engine_sync.dispose()
