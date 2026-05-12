"""Revision base vacia (esquema de app en task-46).

Revision ID: 20260512_0001
Revises:
Create Date: 2026-05-12

"""

from typing import Sequence, Union

revision: str = "20260512_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Sin tablas aun; solo inicializa cadena de migraciones."""
    pass


def downgrade() -> None:
    """Sin tablas aun."""
    pass
