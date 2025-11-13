"""models updated

Revision ID: a8dc3efc871c
Revises: 7a7a63b4655f
Create Date: 2025-05-22 11:12:17.660687

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8dc3efc871c'
down_revision: Union[str, None] = '7a7a63b4655f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
