"""Case insensitive nickname uniqueness; preserve existing names."""
from alembic import op
import sqlalchemy as sa
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    duplicate = op.get_bind().execute(sa.text('SELECT lower(username) FROM users GROUP BY lower(username) HAVING count(*) > 1 LIMIT 1')).first()
    if duplicate:
        raise RuntimeError('Nicknames differing only by case exist. Resolve these accounts before migrating; no nicknames were changed automatically.')
    op.create_index('ux_users_username_lower', 'users', [sa.text('lower(username)')], unique=True)

def downgrade():
    op.drop_index('ux_users_username_lower', table_name='users')
