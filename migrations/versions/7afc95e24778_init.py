"""init

Revision ID: 7afc95e24778
Revises: 
Create Date: 2017-08-03 11:51:08.190298

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7afc95e24778'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('accounts',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('policy_enabled', sa.Boolean(), server_default='FALSE', nullable=False),
    sa.Column('policy_keep_latest', sa.Integer(), server_default='0', nullable=False),
    sa.Column('policy_keep_favourites', sa.Boolean(), server_default='TRUE', nullable=False),
    sa.Column('policy_delete_every', sa.Interval(), server_default='0', nullable=False),
    sa.Column('policy_keep_younger', sa.Interval(), server_default='0', nullable=False),
    sa.Column('display_name', sa.String(), nullable=True),
    sa.Column('screen_name', sa.String(), nullable=True),
    sa.Column('avatar_url', sa.String(), nullable=True),
    sa.Column('last_fetch', sa.DateTime(), server_default='epoch', nullable=True),
    sa.Column('last_delete', sa.DateTime(), server_default='epoch', nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_accounts'))
    )
    op.create_table('oauth_tokens',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('token', sa.String(), nullable=False),
    sa.Column('token_secret', sa.String(), nullable=False),
    sa.Column('account_id', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_oauth_tokens_account_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('token', name=op.f('pk_oauth_tokens'))
    )
    op.create_table('posts',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('body', sa.String(), nullable=True),
    sa.Column('author_id', sa.String(), nullable=False),
    sa.Column('favourite', sa.Boolean(), server_default='FALSE', nullable=False),
    sa.ForeignKeyConstraint(['author_id'], ['accounts.id'], name=op.f('fk_posts_author_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_posts'))
    )
    op.create_table('sessions',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('account_id', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_sessions_account_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_sessions'))
    )
    op.create_table('twitter_archives',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.String(), nullable=False),
    sa.Column('body', sa.LargeBinary(), nullable=False),
    sa.Column('chunks', sa.Integer(), nullable=True),
    sa.Column('chunks_successful', sa.Integer(), server_default='0', nullable=False),
    sa.Column('chunks_failed', sa.Integer(), server_default='0', nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_twitter_archives_account_id_accounts'), onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_twitter_archives'))
    )


def downgrade():
    op.drop_table('twitter_archives')
    op.drop_table('sessions')
    op.drop_table('posts')
    op.drop_table('oauth_tokens')
    op.drop_table('accounts')
