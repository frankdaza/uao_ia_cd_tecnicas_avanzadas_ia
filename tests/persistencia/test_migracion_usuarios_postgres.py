"""
Prueba de integracion: Alembic + PostgreSQL.

Activa con ``EJECUTAR_INTEGRACION_POSTGRES=1``. La URL async se toma de
``INTEGRATION_POSTGRES_ASYNC_URL`` si esta definida (recomendado para Compose
en el host, p. ej. ``postgresql+asyncpg://postgres:postgres@127.0.0.1:15432/app``).
Si no, se usa ``Configuracion`` (``DATABASE_URL`` o ``POSTGRES_*``).

Ejemplo con Postgres de ``docker compose`` publicado en 15432::

    EJECUTAR_INTEGRACION_POSTGRES=1 \\
    INTEGRATION_POSTGRES_ASYNC_URL='postgresql+asyncpg://postgres:postgres@127.0.0.1:15432/app' \\
    uv run pytest tests/persistencia/test_migracion_usuarios_postgres.py -m integration_postgres
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

from src.api.configuracion import obtener_configuracion


@pytest.mark.integration_postgres
def test_alembic_upgrade_crea_tabla_usuarios() -> None:
    if os.environ.get("EJECUTAR_INTEGRACION_POSTGRES", "").strip() != "1":
        pytest.skip(
            "Define EJECUTAR_INTEGRACION_POSTGRES=1 y Postgres accesible "
            "(p. ej. compose en localhost:15432 con POSTGRES_PORT=15432)."
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

    try:
        command.upgrade(alembic_cfg, "head")
        engine = create_engine(sync_url)
        insp = inspect(engine)
        assert insp.has_table("usuarios")
        uniques = {uc["name"] for uc in insp.get_unique_constraints("usuarios")}
        assert "uq_usuarios_documento_identidad" in uniques
    except OperationalError as exc:
        pytest.skip(
            "Postgres no alcanzable con la URL de integracion actual "
            f"(define INTEGRATION_POSTGRES_ASYNC_URL o revisa DATABASE_URL/POSTGRES_*): {exc}"
        )
    finally:
        if "engine" in locals():
            engine.dispose()
