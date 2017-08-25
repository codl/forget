"""add csrf tokens

Revision ID: d97fa46b5560
Revises: f8a153bc809b
Create Date: 2017-08-25 10:10:18.148120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd97fa46b5560'
down_revision = 'f8a153bc809b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sessions', sa.Column('csrf_token', sa.String(), nullable=True))
    op.execute('DELETE FROM sessions')
    op.alter_column('sessions', 'csrf_token', nullable=False)


def downgrade():
    op.drop_column('sessions', 'csrf_token')
