"""add three-way favourite policy

Revision ID: 2bd33abe291c
Revises: 583cdac8eba1
Create Date: 2018-01-03 17:31:03.718648

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2bd33abe291c'
down_revision = '583cdac8eba1'
branch_labels = None
depends_on = None

transitional = sa.table('accounts',
                        sa.column('policy_keep_favourites'),
                        sa.column('old_policy_keep_favourites'))



def upgrade():
    ThreeWayPolicyEnum = sa.Enum('keeponly', 'deleteonly', 'none',
                                name='enum_3way_policy')
    op.alter_column('accounts', 'policy_keep_favourites',
                    new_column_name='old_policy_keep_favourites')
    op.add_column(
        'accounts',
        sa.Column('policy_keep_favourites', ThreeWayPolicyEnum,
                  nullable=False, server_default='none'))

    op.execute(transitional.update()
            .where(transitional.c.old_policy_keep_favourites)
            .values(policy_keep_favourites=op.inline_literal('keeponly')))

    op.drop_column('accounts', 'old_policy_keep_favourites')


def downgrade():
    op.alter_column('accounts', 'policy_keep_favourites',
                    new_column_name='old_policy_keep_favourites')
    op.add_column(
        'accounts',
        sa.Column('policy_keep_favourites', sa.Boolean(),
                  nullable=False, server_default='f'))

    op.execute(transitional.update()
            .where(transitional.c.old_policy_keep_favourites == op.inline_literal('keeponly'))
            .values(policy_keep_favourites=op.inline_literal('t')))

    op.drop_column('accounts', 'old_policy_keep_favourites')
