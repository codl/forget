"""remove post body

Revision ID: 8993e80e7aa3
Revises: c80af843eed3
Create Date: 2017-08-20 18:04:28.516129

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8993e80e7aa3'
down_revision = 'c80af843eed3'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('posts', 'body')


def downgrade():
    op.add_column('posts', sa.Column('body', sa.VARCHAR(), autoincrement=False, nullable=True))
