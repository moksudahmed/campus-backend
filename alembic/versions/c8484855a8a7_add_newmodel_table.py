"""Add NewModel table

Revision ID: c8484855a8a7
Revises: 7393451f8429
Create Date: 2025-05-22 11:36:57.896557

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8484855a8a7'
down_revision: Union[str, None] = '7393451f8429'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
