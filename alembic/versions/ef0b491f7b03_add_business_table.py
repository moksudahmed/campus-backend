"""Add Business table

Revision ID: ef0b491f7b03
Revises: a8dc3efc871c
Create Date: 2025-05-22 11:18:25.462335

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ef0b491f7b03'
down_revision: Union[str, None] = 'a8dc3efc871c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
