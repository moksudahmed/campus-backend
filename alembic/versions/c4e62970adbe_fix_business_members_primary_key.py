"""fix business_members primary key

Revision ID: c4e62970adbe
Revises: eacd39369cfa
Create Date: 2025-05-22 12:13:17.408952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c4e62970adbe'
down_revision: Union[str, None] = 'eacd39369cfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
