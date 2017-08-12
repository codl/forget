"""add last_refresh to match last_fetch and last_delete

Revision ID: 8fac6e10bdb3
Revises: 04da9abf37e2
Create Date: 2017-08-12 22:55:33.004791

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fac6e10bdb3'
down_revision = '04da9abf37e2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('last_refresh', sa.DateTime(), server_default='epoch', nullable=True))


def downgrade():
    op.drop_column('accounts', 'last_refresh')
