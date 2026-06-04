"""Tabla singleton ``config_operativa_taam`` (job recordatorios admin).

Revision ID: 0006_config_operativa_taam
Revises: 0005_medicos
Create Date: 2026-06-04

La fila id=1 se crea en runtime (``obtener_o_crear_desde_env``) con defaults de .env.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_config_operativa_taam"
down_revision: Union[str, Sequence[str], None] = "0005_medicos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config_operativa_taam",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "recordatorios_job_habilitado",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "recordatorios_job_interval_seg",
            sa.Integer(),
            server_default=sa.text("60"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_config_operativa_taam_singleton"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("config_operativa_taam")
