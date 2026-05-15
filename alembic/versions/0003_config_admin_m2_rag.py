"""Columnas RAG (rag_top_k, rag_score_minimo) en config_admin_m2.

Revision ID: 0003_config_admin_m2_rag
Revises: 0002_config_admin_m2
Create Date: 2026-05-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003_config_admin_m2_rag"
down_revision: Union[str, Sequence[str], None] = "0002_config_admin_m2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_top_k", sa.Integer(), nullable=True),
    )
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_score_minimo", sa.Float(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("config_admin_m2", "rag_score_minimo")
    op.drop_column("config_admin_m2", "rag_top_k")
