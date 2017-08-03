"""add policy defaults

Revision ID: 2e3a2882e5a4
Revises: 0983f1227366
Create Date: 2017-08-03 19:54:20.643627

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e3a2882e5a4'
down_revision = '0983f1227366'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('accounts', 'policy_keep_latest', server_default='100')
    op.alter_column('accounts', 'policy_keep_younger', server_default='365 days')
    op.alter_column('accounts', 'policy_delete_every', server_default='30 minutes')


def downgrade():
    op.alter_column('accounts', 'policy_keep_latest', server_default='0')
    op.alter_column('accounts', 'policy_keep_younger', server_default='0')
    op.alter_column('accounts', 'policy_delete_every', server_default='0')
