"""add timestamps

Revision ID: da57b5eb3df7
Revises: 253e9e2dae2d
Create Date: 2017-07-25 10:09:23.233340

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'da57b5eb3df7'
down_revision = '253e9e2dae2d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('account', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('account', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.add_column('sessions', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('sessions', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('users', sa.Column('updated_at', sa.DateTime(), nullable=False))


def downgrade():
    op.drop_column('users', 'updated_at')
    op.drop_column('users', 'created_at')
    op.drop_column('sessions', 'updated_at')
    op.drop_column('sessions', 'created_at')
    op.drop_column('account', 'updated_at')
    op.drop_column('account', 'created_at')
