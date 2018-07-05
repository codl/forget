"""add backoff

Revision ID: c136aa1157f9
Revises: 2bd33abe291c
Create Date: 2018-07-06 00:13:29.726250

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c136aa1157f9'
down_revision = '2bd33abe291c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('backoff_level', sa.Integer(), server_default='0', nullable=False))
    op.add_column('accounts', sa.Column('backoff_until', sa.DateTime(timezone=True), server_default='now', nullable=False))


def downgrade():
    op.drop_column('accounts', 'backoff_until')
    op.drop_column('accounts', 'backoff_level')
