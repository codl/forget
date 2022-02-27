"""remove fetch batch fk

things are real bad if the associated post is deleted and this is nulled
keeping an opaque ID and associated date should work fine
see GH-584

Revision ID: 7b0e9b8e0887
Revises: 740fe24a7712
Create Date: 2022-02-27 11:48:55.107299

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7b0e9b8e0887'
down_revision = '740fe24a7712'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('accounts', sa.Column('fetch_current_batch_end_date', sa.DateTime(timezone=True), nullable=True))
    op.execute('''
        UPDATE accounts SET fetch_current_batch_end_date = posts.created_at
            FROM posts WHERE accounts.fetch_current_batch_end_id == posts.id;
            ''')

    # update ids from "mastodon:69420@chitter.xyz" format to just "69420"
    op.execute('''
        UPDATE accounts SET fetch_current_batch_end_id =
            split_part(
                split_part(fetch_current_batch_end_id, ':', 2)
                    '@', 1);
        ''')

    op.drop_constraint('fk_accounts_fetch_current_batch_end_id_posts', 'accounts', type_='foreignkey')


def downgrade():
    # converts ids like "69420" back to "mastodon:69420@chitter.xyz"
    # i sure hope there isn't a mastodon-compatible out there that can have
    # : or @ in its post ids
    op.execute('''
        WITH accounts_exploded_ids AS (
            SELECT
                id,
                split_part(id, ':', 1) || ':' AS service,
                CASE WHEN position('@' IN id) != 0
                    THEN '@' || split_part(id, @, 2)
                    ELSE ''
                END as instance
            FROM accounts
        )
        UPDATE accounts SET fetch_current_batch_end_id = e.service || fetch_current_batch_end_id || e.instance
        FROM accounts_exploded_ids AS e WHERE e.id = accounts.id AND fetch_current_batch_end_id IS NOT NULL;
    ''')
    op.execute('''
        UPDATE accounts SET fetch_current_batch_end_id = NULL
            WHERE NOT EXISTS (SELECT 1 FROM posts WHERE fetch_current_batch_end_id = posts.id);
            ''')
    op.create_foreign_key('fk_accounts_fetch_current_batch_end_id_posts', 'accounts', 'posts', ['fetch_current_batch_end_id'], ['id'], ondelete='SET NULL')
    op.drop_column('accounts', 'fetch_current_batch_end_date')
