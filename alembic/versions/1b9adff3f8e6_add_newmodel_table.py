"""Add NewModel table

Revision ID: 1b9adff3f8e6
Revises: ef0b491f7b03
Create Date: 2025-05-22 11:22:04.151221

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1b9adff3f8e6'
down_revision: Union[str, None] = 'ef0b491f7b03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
