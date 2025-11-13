"""fix model relationships

Revision ID: eacd39369cfa
Revises: c8484855a8a7
Create Date: 2025-05-22 11:54:28.840616

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eacd39369cfa'
down_revision: Union[str, None] = 'c8484855a8a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
