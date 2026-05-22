"""Auditoria staff y indice de bandeja en alertas_triage (TASK-108).

Revision ID: 0003_alertas_auditoria
Revises: 0002_telegram_updates
Create Date: 2026-05-22
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0003_alertas_auditoria"
down_revision: Union[str, Sequence[str], None] = "0002_telegram_updates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "alertas_triage",
        sa.Column("revisado_staff_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_alertas_triage_revisado_staff",
        "alertas_triage",
        "usuarios_staff",
        ["revisado_staff_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_alertas_triage_revisado_created_at",
        "alertas_triage",
        ["revisado", sa.text("created_at DESC")],
    )
    op.create_index(
        "ix_alertas_triage_caso_id",
        "alertas_triage",
        ["caso_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_alertas_triage_caso_id", table_name="alertas_triage")
    op.drop_index("ix_alertas_triage_revisado_created_at", table_name="alertas_triage")
    op.drop_constraint(
        "fk_alertas_triage_revisado_staff",
        "alertas_triage",
        type_="foreignkey",
    )
    op.drop_column("alertas_triage", "revisado_staff_id")
