"""default next_delete to null

Revision ID: 41ef02e66382
Revises: f95af1a8d89f
Create Date: 2017-08-31 21:19:44.304952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '41ef02e66382'
down_revision = 'f95af1a8d89f'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('accounts', 'next_delete', server_default=None)
    op.execute("UPDATE accounts SET next_delete = NULL where next_delete = 'epoch';")


def downgrade():
    op.alter_column('accounts', 'next_delete', server_default='epoch')
    op.execute("UPDATE accounts SET next_delete = 'epoch' where next_delete IS NULL;")
