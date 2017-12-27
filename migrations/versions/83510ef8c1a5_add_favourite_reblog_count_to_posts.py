"""add favourite, reblog count to posts

Revision ID: 83510ef8c1a5
Revises: c1f7444d0f75
Create Date: 2017-12-27 20:40:31.576201

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '83510ef8c1a5'
down_revision = 'c1f7444d0f75'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('posts', sa.Column('favourites', sa.Integer(), nullable=True))
    op.add_column('posts', sa.Column('reblogs', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('posts', 'reblogs')
    op.drop_column('posts', 'favourites')
