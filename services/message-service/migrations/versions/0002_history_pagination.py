"""Index for cursor pagination within a chat."""
from alembic import op

revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('ix_messages_chat_id_id', 'messages', ['chat_id', 'id'])


def downgrade():
    op.drop_index('ix_messages_chat_id_id', table_name='messages')
