"""empty message

Revision ID: 1003f9df0ae0
Revises: 8c2ce3a66650
Create Date: 2017-07-28 12:32:54.375901

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '1003f9df0ae0'
down_revision = '8c2ce3a66650'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('accounts', 'last_post_fetch', new_column_name='last_fetch')


def downgrade():
    op.alter_column('accounts', 'last_fetch', new_column_name='last_post_fetch')
