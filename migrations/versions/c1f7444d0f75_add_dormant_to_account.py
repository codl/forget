"""add dormant to account

Revision ID: c1f7444d0f75
Revises: 3a0138499994
Create Date: 2017-09-04 21:57:23.648580

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c1f7444d0f75'
down_revision = '3a0138499994'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('dormant', sa.Boolean(), server_default='FALSE', nullable=False))


def downgrade():
    op.drop_column('accounts', 'dormant')
