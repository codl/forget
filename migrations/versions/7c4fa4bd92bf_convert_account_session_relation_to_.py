"""convert account/session relation to many-many

Revision ID: 7c4fa4bd92bf
Revises: 2bd33abe291c
Create Date: 2018-06-07 22:53:25.476476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c4fa4bd92bf'
down_revision = '2bd33abe291c'
branch_labels = None
depends_on = None

sessions = sa.table(
    "sessions",
    sa.Column('id', sa.String),
    sa.Column('account_id', sa.String)
)


def upgrade():
    session_accounts = op.create_table(
        "session_accounts",
        sa.Column('session_id', sa.String),
        sa.Column('account_id', sa.String),
        sa.PrimaryKeyConstraint('session_id', 'account_id', name=op.f('pk_session_accounts')),
        sa.ForeignKeyConstraint(
            ['session_id'], ['sessions.id'],
            name=op.f('fk_session_accounts_session_id_sessions'),
            onupdate='CASCADE', ondelete='CASCADE'
            ),
        sa.ForeignKeyConstraint(
            ['account_id'], ['accounts.id'],
            name=op.f('fk_session_accounts_account_id_accounts'),
            onupdate='CASCADE', ondelete='CASCADE'
            )
        )
    op.execute(
        session_accounts
            .insert()
            .from_select(
                ['session_id', 'account_id'],
                sa.select([sessions])
                )
        )
    op.drop_constraint('fk_sessions_account_id_accounts', 'sessions')
    op.drop_index('ix_sessions_account_id')
    op.alter_column('sessions', 'account_id', new_column_name='current_account_id', nullable=True)
    op.create_foreign_key(
            'fk_sessions_current_account_id_accounts', 'sessions', 'accounts',
            ['current_account_id'], ['id'],
            onupdate='SET NULL', ondelete='SET NULL')


def downgrade():
    op.drop_table("session_accounts")
    op.drop_constraint('fk_sessions_current_account_id_accounts')
    op.alter_column('sessions', 'current_account_id', new_column_name='account_id', nullable=False)
    op.create_foreign_key(
            'fk_sessions_account_id_accounts', 'sessions', 'accounts',
            ['account_id'], ['id'],
            onupdate='CASCADE', ondelete='CASCADE')
    op.create_index('ix_sessions_account_id', 'sessions', ['account_id'])
