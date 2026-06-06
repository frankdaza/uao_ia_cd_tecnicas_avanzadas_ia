"""Tablas adjuntos_mensaje y alertas_adjuntos (multimedia Telegram).

Revision ID: 0009_adjuntos_mensaje
Revises: 0008_vinculos_chat_id_parcial
Create Date: 2026-06-06
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0009_adjuntos_mensaje"
down_revision: Union[str, Sequence[str], None] = "0008_vinculos_chat_id_parcial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "adjuntos_mensaje",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("caso_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("telegram_message_id", sa.BigInteger(), nullable=False),
        sa.Column("telegram_file_id", sa.String(length=256), nullable=False),
        sa.Column("tipo", sa.String(length=16), nullable=False),
        sa.Column("mime_type", sa.String(length=128), nullable=False),
        sa.Column("tamano_bytes", sa.Integer(), nullable=False),
        sa.Column("ruta_relativa", sa.String(length=1024), nullable=False),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("indice_hilo", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "tipo IN ('imagen', 'video', 'audio')",
            name="ck_adjuntos_mensaje_tipo",
        ),
        sa.ForeignKeyConstraint(
            ["caso_id"],
            ["casos_postoperatorio.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_adjuntos_mensaje_caso_indice",
        "adjuntos_mensaje",
        ["caso_id", "indice_hilo"],
    )
    op.create_index(
        "ix_adjuntos_mensaje_telegram_msg",
        "adjuntos_mensaje",
        ["caso_id", "telegram_message_id"],
    )

    op.create_table(
        "alertas_adjuntos",
        sa.Column("alerta_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("adjunto_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["alerta_id"],
            ["alertas_triage.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["adjunto_id"],
            ["adjuntos_mensaje.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("alerta_id", "adjunto_id"),
    )


def downgrade() -> None:
    op.drop_table("alertas_adjuntos")
    op.drop_index("ix_adjuntos_mensaje_telegram_msg", table_name="adjuntos_mensaje")
    op.drop_index("ix_adjuntos_mensaje_caso_indice", table_name="adjuntos_mensaje")
    op.drop_table("adjuntos_mensaje")
