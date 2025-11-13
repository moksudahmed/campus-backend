"""businesses.py creation

Revision ID: d79356725799
Revises: 1874ad68c7cc
Create Date: 2025-05-22 11:01:08.989822

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd79356725799'
down_revision: Union[str, None] = '1874ad68c7cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
