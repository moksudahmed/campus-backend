"""Create inventory logs table and actiontype enum

Revision ID: 4ec9402de123
Revises: 605f2c8a2f6c
Create Date: 2024-09-18 12:17:14.517511

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ec9402de123'
down_revision: Union[str, None] = '605f2c8a2f6c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
