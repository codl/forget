"""replace index on posts.author_id with composite index on author_id and created_at

Revision ID: f63bf9e73bc9
Revises: e769c033e5c9
Create Date: 2017-08-15 23:55:46.945437

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f63bf9e73bc9'
down_revision = 'e769c033e5c9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_posts_author_id_created_at', 'posts', ['author_id', 'created_at'], unique=False)
    op.drop_index('ix_posts_author_id', table_name='posts')


def downgrade():
    op.create_index('ix_posts_author_id', 'posts', ['author_id'], unique=False)
    op.drop_index('ix_posts_author_id_created_at', table_name='posts')
