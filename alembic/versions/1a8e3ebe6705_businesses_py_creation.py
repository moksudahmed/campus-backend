"""businesses.py creation

Revision ID: 1a8e3ebe6705
Revises: 15417f1b91b5
Create Date: 2025-05-22 10:56:36.033647

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a8e3ebe6705'
down_revision: Union[str, None] = '15417f1b91b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
