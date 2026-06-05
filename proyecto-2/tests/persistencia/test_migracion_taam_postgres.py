"""
Prueba de integracion: Alembic + PostgreSQL TAAM.

Activa con ``EJECUTAR_INTEGRACION_POSTGRES=1``. URL recomendada::

    INTEGRATION_POSTGRES_ASYNC_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:15433/taam'
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import OperationalError

from src.configuracion import obtener_configuracion

TABLAS_ESPERADAS = (
    "tipos_procedimiento",
    "casos_postoperatorio",
    "vinculos_telegram",
    "telegram_updates_procesados",
    "alertas_triage",
    "plantillas_recordatorio",
    "recordatorios_enviados",
    "usuarios_staff",
)


@pytest.mark.integration_postgres
def test_alembic_upgrade_crea_esquema_taam() -> None:
    if os.environ.get("EJECUTAR_INTEGRACION_POSTGRES", "").strip() != "1":
        pytest.skip(
            "Define EJECUTAR_INTEGRACION_POSTGRES=1 y Postgres TAAM accesible "
            "(p. ej. compose en localhost:15433)."
        )

    obtener_configuracion.cache_clear()

    url_async = os.environ.get("INTEGRATION_POSTGRES_ASYNC_URL", "").strip()
    if not url_async:
        url_async = obtener_configuracion().url_base_datos_async()
    if not url_async.startswith("postgresql+asyncpg://"):
        pytest.skip("Se esperaba URL async de PostgreSQL para esta prueba.")

    sync_url = (
        make_url(url_async)
        .set(drivername="postgresql+psycopg")
        .render_as_string(hide_password=False)
    )

    raiz = Path(__file__).resolve().parents[2]
    alembic_ini = raiz / "alembic.ini"
    assert alembic_ini.is_file()

    os.environ["ALEMBIC_SYNC_DATABASE_URL"] = sync_url

    alembic_cfg = Config(str(alembic_ini))
    alembic_cfg.set_main_option("script_location", str(raiz / "alembic"))

    engine = None
    try:
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(sync_url)
        insp = inspect(engine)
        for tabla in TABLAS_ESPERADAS:
            assert insp.has_table(tabla), f"Falta tabla {tabla}"
        uniques = {uc["name"] for uc in insp.get_unique_constraints("vinculos_telegram")}
        assert "uq_vinculos_telegram_chat_id" not in uniques
        indices = {idx["name"]: idx for idx in insp.get_indexes("vinculos_telegram")}
        idx_activo = indices.get("uq_vinculos_telegram_chat_id_activo")
        assert idx_activo is not None
        assert idx_activo.get("unique") is True
        assert "telegram_chat_id" in idx_activo.get("column_names", [])
    except OperationalError as exc:
        pytest.skip(
            "Postgres TAAM no alcanzable con la URL de integracion actual: "
            f"{exc}"
        )
    finally:
        if engine is not None:
            engine.dispose()
