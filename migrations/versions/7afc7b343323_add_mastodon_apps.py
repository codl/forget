"""add mastodon apps

Revision ID: 7afc7b343323
Revises: f63bf9e73bc9
Create Date: 2017-08-18 20:36:00.104508

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7afc7b343323'
down_revision = 'f63bf9e73bc9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('mastodon_app',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('instance', sa.String(), nullable=False),
    sa.Column('client_id', sa.String(), nullable=False),
    sa.Column('client_secret', sa.String(), nullable=False),
    sa.Column('protocol', sa.Enum('http', 'https', name='enum_protocol'), nullable=False),
    sa.PrimaryKeyConstraint('instance', name=op.f('pk_mastodon_app'))
    )


def downgrade():
    op.drop_table('mastodon_app')
