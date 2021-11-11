"""add misskey

Revision ID: 740fe24a7712
Revises: af763dccc0b4
Create Date: 2021-11-10 00:13:37.344364

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '740fe24a7712'
down_revision = 'af763dccc0b4'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('misskey_instances',
    sa.Column('instance', sa.String(), nullable=False),
    sa.Column('popularity', sa.Float(), server_default='10', nullable=False),
    sa.PrimaryKeyConstraint('instance', name=op.f('pk_misskey_instances'))
    )
    op.execute("""
        INSERT INTO misskey_instances (instance, popularity) VALUES
            ('misskey.io', 100),
            ('cliq.social', 60),
            ('misskey.dev', 50),
            ('quietplace.xyz', 40),
            ('mk.nixnet.social', 30),
            ('jigglypuff.club', 20);
    """)

    op.create_table('misskey_apps',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('instance', sa.String(), nullable=False),
    sa.Column('miauth', sa.Boolean(), nullable=False),
    sa.Column('client_secret', sa.String(), nullable=True),
    sa.Column('protocol', sa.Enum('http', 'https', name='enum_protocol_misskey'), nullable=False),
    sa.PrimaryKeyConstraint('instance', name=op.f('pk_misskey_apps'))
    )


def downgrade():
    op.drop_table('misskey_instances')
    op.drop_table('misskey_apps')
    op.execute('DROP TYPE enum_protocol_misskey;')
