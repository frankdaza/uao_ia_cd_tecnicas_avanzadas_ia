"""Esquema OLTP inicial TAAM (Modulo 3).

Revision ID: 0001_inicial_taam
Revises:
Create Date: 2026-05-21

PII (enmascarar en listados API staff — TASK-108):
- casos_postoperatorio.paciente_doc_id, paciente_nombre
- alertas_triage.mensaje_paciente_ref

Las tablas de PostgresSaver (checkpointer LangChain) no forman parte de esta revision.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_inicial_taam"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "tipos_procedimiento",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("codigo", sa.String(length=64), nullable=False),
        sa.Column("nombre", sa.String(length=512), nullable=False),
        sa.Column("ruta_pdf", sa.String(length=1024), nullable=True),
        sa.Column("hash_pdf", sa.String(length=128), nullable=True),
        sa.Column("qdrant_collection_version", sa.Integer(), nullable=True),
        sa.Column(
            "indexacion_estado",
            sa.String(length=32),
            server_default=sa.text("'pendiente'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_tipos_procedimiento"),
        sa.UniqueConstraint("codigo", name="uq_tipos_procedimiento_codigo"),
        sa.CheckConstraint(
            "indexacion_estado IN ('pendiente', 'ok', 'error')",
            name="ck_tipos_procedimiento_indexacion_estado",
        ),
    )

    op.create_table(
        "casos_postoperatorio",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("paciente_doc_id", sa.String(length=128), nullable=False),
        sa.Column("paciente_nombre", sa.String(length=512), nullable=False),
        sa.Column("tipo_procedimiento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cirujano_id", sa.String(length=128), nullable=False),
        sa.Column("cirujano_nombre", sa.String(length=512), nullable=False),
        sa.Column("fecha_cirugia", sa.Date(), nullable=False),
        sa.Column("notas_especificas", sa.Text(), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=32),
            server_default=sa.text("'activo'"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tipo_procedimiento_id"],
            ["tipos_procedimiento.id"],
            name="fk_casos_postoperatorio_tipo_procedimiento",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_casos_postoperatorio"),
        sa.CheckConstraint(
            "estado IN ('activo', 'cerrado')",
            name="ck_casos_postoperatorio_estado",
        ),
    )
    op.create_index(
        "ix_casos_postoperatorio_paciente_estado",
        "casos_postoperatorio",
        ["paciente_doc_id", "estado"],
    )

    op.create_table(
        "vinculos_telegram",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("caso_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_chat_id", sa.BigInteger(), nullable=False),
        sa.Column("codigo_emparejamiento", sa.String(length=32), nullable=True),
        sa.Column("codigo_expira_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("vinculado_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["caso_id"],
            ["casos_postoperatorio.id"],
            name="fk_vinculos_telegram_caso",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_vinculos_telegram"),
        sa.UniqueConstraint(
            "telegram_chat_id",
            name="uq_vinculos_telegram_chat_id",
        ),
    )

    op.create_table(
        "alertas_triage",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("caso_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("severidad", sa.String(length=32), nullable=False),
        sa.Column("resumen", sa.String(length=1024), nullable=False),
        sa.Column("mensaje_paciente_ref", sa.Text(), nullable=True),
        sa.Column("tool_trace_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "revisado",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("revisado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["caso_id"],
            ["casos_postoperatorio.id"],
            name="fk_alertas_triage_caso",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_alertas_triage"),
        sa.CheckConstraint(
            "severidad IN ('info', 'seguimiento', 'urgente')",
            name="ck_alertas_triage_severidad",
        ),
    )

    op.create_table(
        "plantillas_recordatorio",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("tipo_procedimiento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tipo", sa.String(length=32), nullable=False),
        sa.Column("offset_horas_desde_cirugia", sa.Integer(), nullable=False),
        sa.Column("texto_plantilla", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(
            ["tipo_procedimiento_id"],
            ["tipos_procedimiento.id"],
            name="fk_plantillas_recordatorio_tipo",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_plantillas_recordatorio"),
        sa.CheckConstraint(
            "tipo IN ('medicacion', 'terapia', 'control')",
            name="ck_plantillas_recordatorio_tipo",
        ),
    )

    op.create_table(
        "recordatorios_enviados",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("caso_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("plantilla_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("programado_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("enviado_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "estado",
            sa.String(length=32),
            server_default=sa.text("'pendiente'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["caso_id"],
            ["casos_postoperatorio.id"],
            name="fk_recordatorios_enviados_caso",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["plantilla_id"],
            ["plantillas_recordatorio.id"],
            name="fk_recordatorios_enviados_plantilla",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_recordatorios_enviados"),
        sa.CheckConstraint(
            "estado IN ('pendiente', 'enviado', 'cancelado', 'error')",
            name="ck_recordatorios_enviados_estado",
        ),
    )

    op.create_table(
        "usuarios_staff",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("nombre", sa.String(length=512), nullable=False),
        sa.Column("rol", sa.String(length=32), nullable=False),
        sa.Column("hash_credencial", sa.String(length=512), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_usuarios_staff"),
        sa.UniqueConstraint("email", name="uq_usuarios_staff_email"),
        sa.CheckConstraint(
            "rol IN ('asistente', 'clinico', 'admin')",
            name="ck_usuarios_staff_rol",
        ),
    )


def downgrade() -> None:
    op.drop_table("usuarios_staff")
    op.drop_table("recordatorios_enviados")
    op.drop_table("plantillas_recordatorio")
    op.drop_table("alertas_triage")
    op.drop_table("vinculos_telegram")
    op.drop_index("ix_casos_postoperatorio_paciente_estado", table_name="casos_postoperatorio")
    op.drop_table("casos_postoperatorio")
    op.drop_table("tipos_procedimiento")
    op.execute("DROP EXTENSION IF EXISTS pgcrypto")
