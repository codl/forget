"""new fetching flags

Revision ID: 4b56cde3ebd7
Revises: c136aa1157f9
Create Date: 2019-02-24 11:53:29.128983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4b56cde3ebd7'
down_revision = 'c136aa1157f9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('fetch_current_batch_end_id', sa.String(), nullable=True))
    op.add_column('accounts', sa.Column('fetch_history_complete', sa.Boolean(), server_default='FALSE', nullable=False))
    op.create_foreign_key(op.f('fk_accounts_fetch_current_batch_end_id_posts'), 'accounts', 'posts', ['fetch_current_batch_end_id'], ['id'], ondelete='SET NULL')


def downgrade():
    op.drop_constraint(op.f('fk_accounts_fetch_current_batch_end_id_posts'), 'accounts', type_='foreignkey')
    op.drop_column('accounts', 'fetch_history_complete')
    op.drop_column('accounts', 'fetch_current_batch_end_id')
