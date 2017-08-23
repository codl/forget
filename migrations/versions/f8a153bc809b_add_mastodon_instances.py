"""add mastodon_instances

Revision ID: f8a153bc809b
Revises: 5fec5f5e8a5e
Create Date: 2017-08-23 11:27:19.223721

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8a153bc809b'
down_revision = '5fec5f5e8a5e'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('mastodon_instances',
    sa.Column('instance', sa.String(), nullable=False),
    sa.Column('popularity', sa.Float(), server_default='10', nullable=False),
    sa.PrimaryKeyConstraint('instance', name=op.f('pk_mastodon_instances'))
    )
    op.execute("""
        INSERT INTO mastodon_instances (instance, popularity) VALUES
            ('mastodon.social', 100),
            ('mastodon.cloud', 90),
            ('social.tchncs.de', 80),
            ('mastodon.xyz', 70),
            ('mstdn.io', 60),
            ('awoo.space', 50),
            ('cybre.space', 40),
            ('mastodon.art', 30)
            ;
    """)


def downgrade():
    op.drop_table('mastodon_instances')
