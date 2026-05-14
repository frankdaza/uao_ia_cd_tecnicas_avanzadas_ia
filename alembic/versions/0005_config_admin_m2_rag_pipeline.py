"""Columnas RAG extendidas (MMR y reranker) en config_admin_m2.

Revision ID: 0005_config_admin_m2_rag_pipeline
Revises: 0004_m2_hist_turnos_max
Create Date: 2026-05-14

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005_config_admin_m2_rag_pipeline"
down_revision: Union[str, Sequence[str], None] = "0004_m2_hist_turnos_max"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_top_k_inicial", sa.Integer(), nullable=True),
    )
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_mmr_habilitado", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_mmr_lambda", sa.Float(), nullable=True),
    )
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_reranker_habilitado", sa.Boolean(), nullable=True),
    )
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_reranker_modelo", sa.String(length=256), nullable=True),
    )
    op.add_column(
        "config_admin_m2",
        sa.Column("rag_reranker_top_n_entrada", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("config_admin_m2", "rag_reranker_top_n_entrada")
    op.drop_column("config_admin_m2", "rag_reranker_modelo")
    op.drop_column("config_admin_m2", "rag_reranker_habilitado")
    op.drop_column("config_admin_m2", "rag_mmr_lambda")
    op.drop_column("config_admin_m2", "rag_mmr_habilitado")
    op.drop_column("config_admin_m2", "rag_top_k_inicial")
