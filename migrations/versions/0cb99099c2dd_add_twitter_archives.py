"""add twitter archives

Revision ID: 0cb99099c2dd
Revises: 92ffc9941fd9
Create Date: 2017-07-30 23:13:48.949949

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0cb99099c2dd'
down_revision = '92ffc9941fd9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('twitter_archives',
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('account_id', sa.String(), nullable=False),
    sa.Column('body', sa.LargeBinary(), nullable=False),
    sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], name=op.f('fk_twitter_archives_account_id_accounts')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_twitter_archives'))
    )


def downgrade():
    op.drop_table('twitter_archives')
