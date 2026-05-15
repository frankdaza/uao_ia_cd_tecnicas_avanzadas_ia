"""Columna rag_reranker_batch_size en config_admin_m2 (TASK-79).

Revision ID: 0006_config_admin_m2_reranker_batch_size
Revises: 0005_config_admin_m2_rag_pipeline
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0006_config_admin_m2_reranker_batch_size"
down_revision: Union[str, Sequence[str], None] = "0005_config_admin_m2_rag_pipeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_reranker_batch_size", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("config_admin_m2", "rag_reranker_batch_size")
