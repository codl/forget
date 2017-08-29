"""add last_delete back

Revision ID: 6fd1f5b43824
Revises: d97fa46b5560
Create Date: 2017-08-29 17:22:00.747220

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6fd1f5b43824'
down_revision = 'd97fa46b5560'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('last_delete', sa.DateTime(), nullable=True))
    op.create_index(op.f('ix_accounts_last_delete'), 'accounts', ['last_delete'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_accounts_last_delete'), table_name='accounts')
    op.drop_column('accounts', 'last_delete')
