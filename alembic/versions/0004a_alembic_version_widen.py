"""Amplia alembic_version.version_num para revisiones > 32 caracteres.

Revision ID: 0004a_alembic_vnum_128
Revises: 0004_m2_hist_turnos_max
Create Date: 2026-05-15

El valor por defecto VARCHAR(32) de Alembic trunca IDs como 0005_config_admin_m2_rag_pipeline.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004a_alembic_vnum_128"
down_revision: Union[str, Sequence[str], None] = "0004_m2_hist_turnos_max"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=128),
        existing_nullable=False,
    )


def downgrade() -> None:
    # Solo es seguro si ninguna revision almacenada supera 32 caracteres.
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=128),
        type_=sa.String(length=32),
        existing_nullable=False,
    )
