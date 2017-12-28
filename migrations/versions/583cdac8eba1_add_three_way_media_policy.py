"""add three-way media policy

Revision ID: 583cdac8eba1
Revises: 7e255d4ea34d
Create Date: 2017-12-28 00:46:56.023649

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '583cdac8eba1'
down_revision = '7e255d4ea34d'
branch_labels = None
depends_on = None

transitional = sa.table('accounts',
                        sa.column('policy_keep_media'),
                        sa.column('old_policy_keep_media'))



def upgrade():
    ThreeWayPolicyEnum = sa.Enum('keeponly', 'deleteonly', 'none',
                                name='enum_3way_policy')
    op.execute("""
        CREATE TYPE enum_3way_policy AS ENUM ('keeponly', 'deleteonly', 'none')
    """)
    op.alter_column('accounts', 'policy_keep_media',
                    new_column_name='old_policy_keep_media')
    op.add_column(
        'accounts',
        sa.Column('policy_keep_media', ThreeWayPolicyEnum,
                  nullable=False, server_default='none'))

    op.execute(transitional.update()
            .where(transitional.c.old_policy_keep_media)
            .values(policy_keep_media=op.inline_literal('keeponly')))

    op.drop_column('accounts', 'old_policy_keep_media')


def downgrade():
    op.alter_column('accounts', 'policy_keep_media',
                    new_column_name='old_policy_keep_media')
    op.add_column(
        'accounts',
        sa.Column('policy_keep_media', sa.Boolean(),
                  nullable=False, server_default='f'))

    op.execute(transitional.update()
            .where(transitional.c.old_policy_keep_media == op.inline_literal('keeponly'))
            .values(policy_keep_media=op.inline_literal('t')))

    op.drop_column('accounts', 'old_policy_keep_media')
    op.execute("""
        DROP TYPE enum_3way_policy
    """)
