"""Friend requests and accepted relationships."""
from alembic import op
import sqlalchemy as sa
revision = '0002'
down_revision = '0001'
branch_labels = depends_on = None


def upgrade():
    op.create_table('friendships',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('pair_key', sa.String(50), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('pair_key', name='uq_friendship_pair'),
        sa.CheckConstraint('requester_id != recipient_id', name='ck_friendship_distinct'),
        sa.CheckConstraint("status IN ('pending', 'accepted')", name='ck_friendship_status'))
    op.create_index('ix_friendships_requester_id', 'friendships', ['requester_id'])
    op.create_index('ix_friendships_recipient_id', 'friendships', ['recipient_id'])


def downgrade():
    op.drop_table('friendships')
