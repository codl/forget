"""make token secret nullable

Revision ID: c80af843eed3
Revises: fbdc10b29df9
Create Date: 2017-08-18 21:25:17.933702

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c80af843eed3'
down_revision = 'fbdc10b29df9'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('oauth_tokens', 'token_secret',
               existing_type=sa.VARCHAR(),
               nullable=True)


def downgrade():
    op.alter_column('oauth_tokens', 'token_secret',
               existing_type=sa.VARCHAR(),
               nullable=False)
