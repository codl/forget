"""it's supposed to be plural, dummy

Revision ID: fbdc10b29df9
Revises: 7afc7b343323
Create Date: 2017-08-18 20:39:39.119165

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'fbdc10b29df9'
down_revision = '7afc7b343323'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('ALTER TABLE mastodon_app RENAME TO mastodon_apps')


def downgrade():
    op.execute('ALTER TABLE mastodon_apps RENAME TO mastodon_app')
