"""businesses.py creation

Revision ID: 3a7d8546ee9a
Revises: d79356725799
Create Date: 2025-05-22 11:01:19.846162

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3a7d8546ee9a'
down_revision: Union[str, None] = 'd79356725799'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
