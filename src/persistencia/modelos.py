"""Modelos ORM SQLAlchemy 2.x (Modulo 2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base declarativa compartida por tablas de aplicacion."""


class Usuario(Base):
    """
    Usuario identificado por documento de identidad unico.

    El valor por defecto de ``id`` es ``gen_random_uuid()`` en PostgreSQL
    (definido en migracion Alembic y reflejado aqui con ``server_default``).
    """

    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    documento_identidad: Mapped[str] = mapped_column(String(128), unique=True)
    nombre: Mapped[str] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )


class ConfigAdminM2(Base):
    """
    Fila singleton (id=1) con overrides de configuracion runtime del agente M2.

    Valores ``NULL`` en columnas de datos significan *sin override* (se toma archivo
    ``config/router_meta_prompt.json``, variables de entorno o constantes de codigo).
    """

    __tablename__ = "config_admin_m2"
    __table_args__ = (CheckConstraint("id = 1", name="ck_config_admin_m2_singleton"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )
    modelo_llm_router: Mapped[str | None] = mapped_column(String(128), nullable=True)
    modelo_llm_compositor: Mapped[str | None] = mapped_column(String(128), nullable=True)
    temperatura_router: Mapped[float | None] = mapped_column(Float, nullable=True)
    temperatura_compositor: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_p_router: Mapped[float | None] = mapped_column(Float, nullable=True)
    top_p_compositor: Mapped[float | None] = mapped_column(Float, nullable=True)
    model_kwargs_router: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    model_kwargs_compositor: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    meta_prompt_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    prompt_institucional: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
