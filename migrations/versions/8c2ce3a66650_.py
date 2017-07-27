"""empty message

Revision ID: 8c2ce3a66650
Revises: a5718ca3ead1
Create Date: 2017-07-27 23:35:48.842519

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8c2ce3a66650'
down_revision = 'a5718ca3ead1'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_constraint('fk_posts_author_remote_id_accounts', 'posts', type_='foreignkey')
    op.alter_column('posts', 'author_remote_id', new_column_name='author_id')
    op.create_foreign_key(op.f('fk_posts_author_id_accounts'), 'posts', 'accounts', ['author_id'], ['remote_id'])


def downgrade():
    op.drop_constraint(op.f('fk_posts_author_id_accounts'), 'posts', type_='foreignkey')
    op.alter_column('posts', 'author_id', new_column_name='author_remote_id')
    op.create_foreign_key('fk_posts_author_remote_id_accounts', 'posts', 'accounts', ['author_remote_id'], ['remote_id'])
