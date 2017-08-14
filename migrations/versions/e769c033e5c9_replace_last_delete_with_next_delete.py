"""replace last_delete with next_delete

Revision ID: e769c033e5c9
Revises: 6d298e6406f2
Create Date: 2017-08-14 20:51:02.248343

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e769c033e5c9'
down_revision = '6d298e6406f2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('next_delete', sa.DateTime(), server_default='epoch', nullable=True))
    op.execute('UPDATE accounts SET next_delete = last_delete + policy_delete_every;')
    op.create_index(op.f('ix_accounts_next_delete'), 'accounts', ['next_delete'], unique=False)
    op.drop_index('ix_accounts_last_delete', table_name='accounts')
    op.drop_column('accounts', 'last_delete')


def downgrade():
    op.add_column('accounts', sa.Column('last_delete', postgresql.TIMESTAMP(), server_default=sa.text("'1970-01-01 00:00:00'::timestamp without time zone"), autoincrement=False, nullable=True))
    op.execute('UPDATE accounts SET last__delete = next_delete - policy_delete_every;')
    op.create_index('ix_accounts_last_delete', 'accounts', ['last_delete'], unique=False)
    op.drop_index(op.f('ix_accounts_next_delete'), table_name='accounts')
    op.drop_column('accounts', 'next_delete')
