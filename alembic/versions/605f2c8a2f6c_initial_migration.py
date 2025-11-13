"""Initial migration

Revision ID: 605f2c8a2f6c
Revises: 
Create Date: 2024-08-10 22:09:26.160759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '605f2c8a2f6c'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
     # Create users table
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('username', sa.String(50), unique=True, index=True, nullable=False),
        sa.Column('email', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_superuser', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False)
    )

    # Create products table
    op.create_table(
        'product',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('title', sa.String, index=True, nullable=False),
        sa.Column('unit_price', sa.Float, nullable=False),
        sa.Column('stock', sa.Integer, nullable=False)
    )

    # Create sales table
    op.create_table(
        'sale',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('user.id'), nullable=False),
        sa.Column('total', sa.Float, nullable=False),  # Add this line
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('discount', sa.Integer, nullable=False),  # Add this line
     
    )
    
    # Create sale_product relationship table
    op.create_table(
        'sale_product',
        sa.Column('sale_id', sa.Integer, sa.ForeignKey('sale.id', ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column('product_id', sa.Integer, sa.ForeignKey('product.id', ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column('quantity', sa.Integer, nullable=False),
        sa.Column('total_price', sa.Float, nullable=False),
    )

def downgrade() -> None:
    # Drop sale_product table
    op.drop_table('sale_product')

    # Drop sales table
    op.drop_table('sale')

    # Drop products table
    op.drop_table('product')

    # Drop users table
    op.drop_table('user')
