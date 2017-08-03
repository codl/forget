"""add reported post count column to account

Revision ID: 0983f1227366
Revises: 7afc95e24778
Create Date: 2017-08-03 19:16:55.883575

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0983f1227366'
down_revision = '7afc95e24778'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('reported_post_count', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('accounts', 'reported_post_count')
