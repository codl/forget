"""add reason to account

Revision ID: 3a0138499994
Revises: 41ef02e66382
Create Date: 2017-09-02 19:46:14.035946

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a0138499994'
down_revision = '41ef02e66382'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('reason', sa.String(), nullable=True))


def downgrade():
    op.drop_column('accounts', 'reason')
