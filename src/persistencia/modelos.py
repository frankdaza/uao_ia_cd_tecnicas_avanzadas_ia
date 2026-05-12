"""Modelos ORM SQLAlchemy 2.x (Modulo 2)."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, func, text
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
