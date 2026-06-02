"""Tabla catalogo ``medicos`` (cirujanos administrables).

Revision ID: 0005_medicos
Revises: 0004_formato_protocolo_taam
Create Date: 2026-06-02

downgrade() elimina la tabla ``medicos`` (sin FK desde casos en esta revision).
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0005_medicos"
down_revision: Union[str, Sequence[str], None] = "0004_formato_protocolo_taam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "medicos",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("codigo_registro", sa.String(length=64), nullable=False),
        sa.Column("nombre_completo", sa.String(length=512), nullable=False),
        sa.Column("especialidad", sa.String(length=256), nullable=True),
        sa.Column(
            "activo",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name="pk_medicos"),
        sa.UniqueConstraint("codigo_registro", name="uq_medicos_codigo_registro"),
    )
    op.create_index("ix_medicos_activo", "medicos", ["activo"])


def downgrade() -> None:
    op.drop_index("ix_medicos_activo", table_name="medicos")
    op.drop_table("medicos")
