"""Columna ``desvinculado_at`` en vinculos_telegram (soft unlink admin).

Revision ID: 0007_vinculos_desvinculado_at
Revises: 0006_config_operativa_taam
Create Date: 2026-06-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007_vinculos_desvinculado_at"
down_revision: Union[str, Sequence[str], None] = "0006_config_operativa_taam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "vinculos_telegram",
        sa.Column("desvinculado_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("vinculos_telegram", "desvinculado_at")
