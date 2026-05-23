"""Columna historial_turnos_max en config_admin_m2.

Revision ID: 0004_m2_hist_turnos_max
Revises: 0003_config_admin_m2_rag
Create Date: 2026-05-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_m2_hist_turnos_max"
down_revision: Union[str, Sequence[str], None] = "0003_config_admin_m2_rag"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "config_admin_m2",
        sa.Column("historial_turnos_max", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("config_admin_m2", "historial_turnos_max")
