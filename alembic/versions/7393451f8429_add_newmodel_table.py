"""Add NewModel table

Revision ID: 7393451f8429
Revises: 1b9adff3f8e6
Create Date: 2025-05-22 11:24:21.533631

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7393451f8429'
down_revision: Union[str, None] = '1b9adff3f8e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
