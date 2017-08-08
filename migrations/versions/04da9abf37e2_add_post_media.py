"""add post media

Revision ID: 04da9abf37e2
Revises: 2e3a2882e5a4
Create Date: 2017-08-08 15:15:50.911420

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '04da9abf37e2'
down_revision = '2e3a2882e5a4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('policy_keep_media', sa.Boolean(), server_default='FALSE', nullable=False))
    op.add_column('posts', sa.Column('has_media', sa.Boolean(), server_default='FALSE', nullable=False))
    # ### end Alembic commands ###


def downgrade():
    op.drop_column('posts', 'has_media')
    op.drop_column('accounts', 'policy_keep_media')
