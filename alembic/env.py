"""Entorno Alembic: motor sincrono `postgresql+psycopg` alineado con Configuracion."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from src.api.configuracion import obtener_configuracion

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def obtener_url_sincrona() -> str:
    """URL sincrona para migraciones (Alembic no usa asyncpg)."""
    if override := os.environ.get("ALEMBIC_SYNC_DATABASE_URL", "").strip():
        return override
    url_async = obtener_configuracion().url_base_datos_async()
    if url_async.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + url_async.removeprefix("postgresql+asyncpg://")
    return url_async


def run_migrations_offline() -> None:
    url = obtener_url_sincrona()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = obtener_url_sincrona()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
