"""Enforce one private chat per unordered pair of users."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    pairs = {}
    rows = connection.execute(sa.text('''
        SELECT c.id, COUNT(m.id) AS members,
               MIN(m.auth_user_id) AS first_user, MAX(m.auth_user_id) AS second_user
        FROM chats c LEFT JOIN chat_members m ON m.chat_id = c.id
        WHERE c.type = 'PRIVATE'
        GROUP BY c.id
    ''')).mappings()
    # Refuse ambiguous legacy data; never merge/delete chats or lose messages.
    for row in rows:
        if row['members'] != 2 or row['first_user'] == row['second_user']:
            raise RuntimeError(f"Private chat {row['id']} must have two distinct members")
        key = f"{row['first_user']}:{row['second_user']}"
        if key in pairs:
            raise RuntimeError(f"Duplicate private chats {pairs[key]} and {row['id']}; resolve before migration")
        pairs[key] = row['id']
    op.add_column('chats', sa.Column('private_key', sa.String(50), nullable=True))
    for key, chat_id in pairs.items():
        connection.execute(sa.text('UPDATE chats SET private_key = :key WHERE id = :id'), {'key': key, 'id': chat_id})
    with op.batch_alter_table('chats') as batch:
        batch.create_unique_constraint('uq_chat_private_key', ['private_key'])


def downgrade():
    with op.batch_alter_table('chats') as batch:
        batch.drop_constraint('uq_chat_private_key', type_='unique')
        batch.drop_column('private_key')
