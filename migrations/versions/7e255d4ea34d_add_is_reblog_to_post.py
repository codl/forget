"""add is_reblog to Post

Revision ID: 7e255d4ea34d
Revises: 83510ef8c1a5
Create Date: 2017-12-27 21:18:48.988601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e255d4ea34d'
down_revision = '83510ef8c1a5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('is_reblog', sa.Boolean(), server_default='FALSE', nullable=False))


def downgrade():
    op.drop_column('posts', 'is_reblog')
