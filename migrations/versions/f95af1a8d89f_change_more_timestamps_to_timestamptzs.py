"""change more timestamps to timestamptzs

Revision ID: f95af1a8d89f
Revises: 90b5b84abc6a
Create Date: 2017-08-31 17:00:20.538070

"""
from alembic import op
from sqlalchemy.types import DateTime


# revision identifiers, used by Alembic.
revision = 'f95af1a8d89f'
down_revision = '90b5b84abc6a'
branch_labels = None
depends_on = None


def upgrade():
    for column in ('last_fetch', 'last_refresh', 'last_delete', 'next_delete'):
        op.alter_column('accounts', column, type_=DateTime(timezone=True))


def downgrade():
    for column in ('last_fetch', 'last_refresh', 'last_delete', 'next_delete'):
        op.alter_column('accounts', column, type_=DateTime(timezone=False))
