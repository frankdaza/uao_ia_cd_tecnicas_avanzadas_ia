"""Columna formato_protocolo en tipos_procedimiento (PDF o Markdown).

Revision ID: 0004_formato_protocolo_taam
Revises: 0003_alertas_auditoria
Create Date: 2026-06-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_formato_protocolo_taam"
down_revision: Union[str, Sequence[str], None] = "0003_alertas_auditoria"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "tipos_procedimiento",
        sa.Column(
            "formato_protocolo",
            sa.String(length=16),
            server_default=sa.text("'pdf'"),
            nullable=False,
        ),
    )
    op.create_check_constraint(
        "ck_tipos_procedimiento_formato_protocolo",
        "tipos_procedimiento",
        "formato_protocolo IN ('pdf', 'markdown')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_tipos_procedimiento_formato_protocolo",
        "tipos_procedimiento",
        type_="check",
    )
    op.drop_column("tipos_procedimiento", "formato_protocolo")
