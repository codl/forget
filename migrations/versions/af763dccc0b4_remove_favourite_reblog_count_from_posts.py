"""remove favourite, reblog count from posts

Revision ID: af763dccc0b4
Revises: 4b56cde3ebd7
Create Date: 2021-05-14 19:45:37.429645

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'af763dccc0b4'
down_revision = '4b56cde3ebd7'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('posts', 'reblogs')
    op.drop_column('posts', 'favourites')


def downgrade():
    op.add_column('posts', sa.Column('favourites', sa.Integer(), nullable=True))
    op.add_column('posts', sa.Column('reblogs', sa.Integer(), nullable=True))
