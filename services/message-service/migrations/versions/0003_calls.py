"""Persistent call history; media itself is peer-to-peer."""
from alembic import op
import sqlalchemy as sa
revision = '0003'
down_revision = '0002'
branch_labels = depends_on = None


def upgrade():
    op.create_table('calls',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('chat_id', sa.Integer(), nullable=False),
        sa.Column('caller_id', sa.Integer(), nullable=False),
        sa.Column('callee_id', sa.Integer(), nullable=False),
        sa.Column('media', sa.String(8), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('answered_at', sa.DateTime(timezone=True)),
        sa.Column('ended_at', sa.DateTime(timezone=True)))
    for column in ('chat_id', 'caller_id', 'callee_id'):
        op.create_index('ix_calls_' + column, 'calls', [column])


def downgrade():
    op.drop_table('calls')
