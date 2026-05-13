"""Tabla singleton config_admin_m2 (overrides runtime panel admin M2).

Revision ID: 0002_config_admin_m2
Revises: 0001_create_usuarios
Create Date: 2026-05-13

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_config_admin_m2"
down_revision: Union[str, Sequence[str], None] = "0001_create_usuarios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "config_admin_m2",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "version",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("modelo_llm_router", sa.String(length=128), nullable=True),
        sa.Column("modelo_llm_compositor", sa.String(length=128), nullable=True),
        sa.Column("temperatura_router", sa.Float(), nullable=True),
        sa.Column("temperatura_compositor", sa.Float(), nullable=True),
        sa.Column("top_p_router", sa.Float(), nullable=True),
        sa.Column("top_p_compositor", sa.Float(), nullable=True),
        sa.Column("model_kwargs_router", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "model_kwargs_compositor",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("meta_prompt_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("prompt_institucional", sa.Text(), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint("id = 1", name="ck_config_admin_m2_singleton"),
        sa.PrimaryKeyConstraint("id", name="pk_config_admin_m2"),
    )


def downgrade() -> None:
    op.drop_table("config_admin_m2")
