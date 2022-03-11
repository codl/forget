"""add celery checkin

Revision ID: 2a46ac75281c
Revises: 7b0e9b8e0887
Create Date: 2022-03-04 20:43:58.455920

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a46ac75281c'
down_revision = '7b0e9b8e0887'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('worker_checkins',
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('id', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_worker_checkins'))
    )


def downgrade():
    op.drop_table('worker_checkins')
