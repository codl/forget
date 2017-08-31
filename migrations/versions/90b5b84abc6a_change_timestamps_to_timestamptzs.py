"""change timestamps to timestamptzs

Revision ID: 90b5b84abc6a
Revises: 6fd1f5b43824
Create Date: 2017-08-31 16:46:16.785021

"""
from alembic import op
from sqlalchemy.types import DateTime


# revision identifiers, used by Alembic.
revision = '90b5b84abc6a'
down_revision = '6fd1f5b43824'
branch_labels = None
depends_on = None


def upgrade():
    for table in ('accounts', 'oauth_tokens', 'posts', 'sessions',
                  'twitter_archives', 'mastodon_apps'):
        for column in ('created_at', 'updated_at'):
            op.alter_column(table, column, type_=DateTime(timezone=True))


def downgrade():
    for table in ('account', 'oauth_tokens', 'posts', 'sessions',
                  'twitter_archives', 'mastodon_apps'):
        for column in ('created_at', 'updated_at'):
            op.alter_column(table, column, type_=DateTime(timezone=False))
