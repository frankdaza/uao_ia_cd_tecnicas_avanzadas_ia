"""Modelos ORM SQLAlchemy 2.x (TAAM / Modulo 3)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Valores cerrados documentados en migracion y casos de uso TAAM.
INDEXACION_ESTADOS = ("pendiente", "ok", "error")
ESTADOS_CASO = ("activo", "cerrado")
SEVERIDADES_TRIAGE = ("info", "seguimiento", "urgente")
TIPOS_PLANTILLA = ("medicacion", "terapia", "control")
ESTADOS_RECORDATORIO = ("pendiente", "enviado", "cancelado", "error")
ROLES_STAFF = ("asistente", "clinico", "admin")


class Base(DeclarativeBase):
    """Base declarativa compartida por tablas OLTP TAAM."""


class TipoProcedimiento(Base):
    """Catalogo de procedimientos quirurgicos (UC-MVP-01)."""

    __tablename__ = "tipos_procedimiento"
    __table_args__ = (
        CheckConstraint(
            f"indexacion_estado IN {INDEXACION_ESTADOS}",
            name="ck_tipos_procedimiento_indexacion_estado",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    codigo: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(512), nullable=False)
    ruta_pdf: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    hash_pdf: Mapped[str | None] = mapped_column(String(128), nullable=True)
    qdrant_collection_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    indexacion_estado: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'pendiente'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    casos: Mapped[list[CasoPostoperatorio]] = relationship(back_populates="tipo_procedimiento")
    plantillas: Mapped[list[PlantillaRecordatorio]] = relationship(
        back_populates="tipo_procedimiento"
    )


class CasoPostoperatorio(Base):
    """Caso quirurgico de un paciente (UC-MVP-02)."""

    __tablename__ = "casos_postoperatorio"
    __table_args__ = (
        CheckConstraint(
            f"estado IN {ESTADOS_CASO}",
            name="ck_casos_postoperatorio_estado",
        ),
        Index("ix_casos_postoperatorio_paciente_estado", "paciente_doc_id", "estado"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    paciente_doc_id: Mapped[str] = mapped_column(String(128), nullable=False)
    paciente_nombre: Mapped[str] = mapped_column(String(512), nullable=False)
    tipo_procedimiento_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tipos_procedimiento.id", ondelete="RESTRICT"),
        nullable=False,
    )
    cirujano_id: Mapped[str] = mapped_column(String(128), nullable=False)
    cirujano_nombre: Mapped[str] = mapped_column(String(512), nullable=False)
    fecha_cirugia: Mapped[date] = mapped_column(Date, nullable=False)
    notas_especificas: Mapped[str | None] = mapped_column(Text, nullable=True)
    estado: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'activo'"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    tipo_procedimiento: Mapped[TipoProcedimiento] = relationship(back_populates="casos")
    vinculos_telegram: Mapped[list[VinculoTelegram]] = relationship(back_populates="caso")
    alertas: Mapped[list[AlertaTriage]] = relationship(back_populates="caso")
    recordatorios: Mapped[list[RecordatorioEnviado]] = relationship(back_populates="caso")


class VinculoTelegram(Base):
    """Emparejamiento paciente Telegram ↔ caso activo (UC-MVP-02)."""

    __tablename__ = "vinculos_telegram"

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    caso_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("casos_postoperatorio.id", ondelete="CASCADE"),
        nullable=False,
    )
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    codigo_emparejamiento: Mapped[str | None] = mapped_column(String(32), nullable=True)
    codigo_expira_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    vinculado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    caso: Mapped[CasoPostoperatorio] = relationship(back_populates="vinculos_telegram")


class TelegramUpdateProcesado(Base):
    """Idempotencia de updates Telegram (TASK-106)."""

    __tablename__ = "telegram_updates_procesados"

    update_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class AlertaTriage(Base):
    """Alerta de triage para revision del staff (UC-MVP-05)."""

    __tablename__ = "alertas_triage"
    __table_args__ = (
        CheckConstraint(
            f"severidad IN {SEVERIDADES_TRIAGE}",
            name="ck_alertas_triage_severidad",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    caso_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("casos_postoperatorio.id", ondelete="CASCADE"),
        nullable=False,
    )
    severidad: Mapped[str] = mapped_column(String(32), nullable=False)
    resumen: Mapped[str] = mapped_column(String(1024), nullable=False)
    mensaje_paciente_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    tool_trace_json: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB(astext_type=Text()), "postgresql"),
        nullable=True,
    )
    revisado: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("false"),
    )
    revisado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    caso: Mapped[CasoPostoperatorio] = relationship(back_populates="alertas")


class PlantillaRecordatorio(Base):
    """Plantilla de recordatorio asociada a un tipo de procedimiento (UC-MVP-04)."""

    __tablename__ = "plantillas_recordatorio"
    __table_args__ = (
        CheckConstraint(
            f"tipo IN {TIPOS_PLANTILLA}",
            name="ck_plantillas_recordatorio_tipo",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    tipo_procedimiento_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("tipos_procedimiento.id", ondelete="CASCADE"),
        nullable=False,
    )
    tipo: Mapped[str] = mapped_column(String(32), nullable=False)
    offset_horas_desde_cirugia: Mapped[int] = mapped_column(Integer, nullable=False)
    texto_plantilla: Mapped[str] = mapped_column(Text, nullable=False)

    tipo_procedimiento: Mapped[TipoProcedimiento] = relationship(back_populates="plantillas")
    recordatorios: Mapped[list[RecordatorioEnviado]] = relationship(
        back_populates="plantilla"
    )


class RecordatorioEnviado(Base):
    """Trazabilidad de recordatorios programados o enviados (UC-MVP-04)."""

    __tablename__ = "recordatorios_enviados"
    __table_args__ = (
        CheckConstraint(
            f"estado IN {ESTADOS_RECORDATORIO}",
            name="ck_recordatorios_enviados_estado",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    caso_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("casos_postoperatorio.id", ondelete="CASCADE"),
        nullable=False,
    )
    plantilla_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("plantillas_recordatorio.id", ondelete="RESTRICT"),
        nullable=False,
    )
    programado_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    enviado_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    estado: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'pendiente'"),
    )

    caso: Mapped[CasoPostoperatorio] = relationship(back_populates="recordatorios")
    plantilla: Mapped[PlantillaRecordatorio] = relationship(back_populates="recordatorios")


class UsuarioStaff(Base):
    """Usuario del panel staff (auth JWT en TASK-105)."""

    __tablename__ = "usuarios_staff"
    __table_args__ = (
        CheckConstraint(
            f"rol IN {ROLES_STAFF}",
            name="ck_usuarios_staff_rol",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(512), nullable=False)
    rol: Mapped[str] = mapped_column(String(32), nullable=False)
    hash_credencial: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
