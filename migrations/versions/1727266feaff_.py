"""empty message

Revision ID: 1727266feaff
Revises: 1003f9df0ae0
Create Date: 2017-07-29 11:09:02.743619

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1727266feaff'
down_revision = '1003f9df0ae0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('remote_screen_name', sa.String(), nullable=True))


def downgrade():
    op.drop_column('accounts', 'remote_screen_name')
