"""Tabla de idempotencia para webhook Telegram (TASK-106).

Revision ID: 0002_telegram_updates
Revises: 0001_inicial_taam
Create Date: 2026-05-21
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_telegram_updates"
down_revision: Union[str, Sequence[str], None] = "0001_inicial_taam"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "telegram_updates_procesados",
        sa.Column("update_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("update_id", name="pk_telegram_updates_procesados"),
    )


def downgrade() -> None:
    op.drop_table("telegram_updates_procesados")
