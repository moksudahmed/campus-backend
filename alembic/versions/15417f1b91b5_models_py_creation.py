"""models.py creation

Revision ID: 15417f1b91b5
Revises: 4ec9402de123
Create Date: 2025-05-22 10:55:30.069328

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '15417f1b91b5'
down_revision: Union[str, None] = '4ec9402de123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
