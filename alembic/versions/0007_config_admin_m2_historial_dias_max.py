"""Columna historial_dias_max en config_admin_m2 (ventana temporal alineada con admin).

Revision ID: 0007_config_admin_m2_historial_dias_max
Revises: 0006_config_admin_m2_reranker_batch_size
Create Date: 2026-05-16

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_config_admin_m2_historial_dias_max"
down_revision: Union[str, Sequence[str], None] = "0006_config_admin_m2_reranker_batch_size"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "config_admin_m2",
        sa.Column("historial_dias_max", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("config_admin_m2", "historial_dias_max")
