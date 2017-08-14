"""add some probably good indexes (???)

Revision ID: 6d298e6406f2
Revises: 8fac6e10bdb3
Create Date: 2017-08-14 20:27:49.103672

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6d298e6406f2'
down_revision = '8fac6e10bdb3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_accounts_last_delete'), 'accounts', ['last_delete'], unique=False)
    op.create_index(op.f('ix_accounts_last_fetch'), 'accounts', ['last_fetch'], unique=False)
    op.create_index(op.f('ix_accounts_last_refresh'), 'accounts', ['last_refresh'], unique=False)
    op.create_index(op.f('ix_oauth_tokens_account_id'), 'oauth_tokens', ['account_id'], unique=False)
    op.create_index(op.f('ix_posts_author_id'), 'posts', ['author_id'], unique=False)
    op.create_index(op.f('ix_sessions_account_id'), 'sessions', ['account_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_sessions_account_id'), table_name='sessions')
    op.drop_index(op.f('ix_posts_author_id'), table_name='posts')
    op.drop_index(op.f('ix_oauth_tokens_account_id'), table_name='oauth_tokens')
    op.drop_index(op.f('ix_accounts_last_refresh'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_last_fetch'), table_name='accounts')
    op.drop_index(op.f('ix_accounts_last_delete'), table_name='accounts')
