"""add post.direct and account.policy_keep_direct

Revision ID: 5fec5f5e8a5e
Revises: 8993e80e7aa3
Create Date: 2017-08-20 18:16:26.682744

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5fec5f5e8a5e'
down_revision = '8993e80e7aa3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('policy_keep_direct', sa.Boolean(), server_default='TRUE', nullable=False))
    op.add_column('posts', sa.Column('direct', sa.Boolean(), server_default='FALSE', nullable=False))


def downgrade():
    op.drop_column('posts', 'direct')
    op.drop_column('accounts', 'policy_keep_direct')
