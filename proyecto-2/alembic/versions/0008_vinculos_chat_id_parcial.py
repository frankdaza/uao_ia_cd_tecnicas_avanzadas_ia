"""Indice unico parcial en telegram_chat_id (solo vinculos no desvinculados).

Revision ID: 0008_vinculos_chat_id_parcial
Revises: 0007_vinculos_desvinculado_at
Create Date: 2026-06-05
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0008_vinculos_chat_id_parcial"
down_revision: Union[str, Sequence[str], None] = "0007_vinculos_desvinculado_at"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint(
        "uq_vinculos_telegram_chat_id",
        "vinculos_telegram",
        type_="unique",
    )
    op.create_index(
        "uq_vinculos_telegram_chat_id_activo",
        "vinculos_telegram",
        ["telegram_chat_id"],
        unique=True,
        postgresql_where=sa.text("desvinculado_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_vinculos_telegram_chat_id_activo",
        table_name="vinculos_telegram",
    )
    op.create_unique_constraint(
        "uq_vinculos_telegram_chat_id",
        "vinculos_telegram",
        ["telegram_chat_id"],
    )
