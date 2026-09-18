"""initial schema

Revision ID: 0001
Revises: 
Create Date: 2026-09-19 00:09:59.492644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('chats',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum('PRIVATE', 'GROUP', name='chattype'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('chat_members',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('auth_user_id', sa.Integer(), nullable=False),
    sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('chat_id', 'auth_user_id', name='uq_chat_member')
    )
    op.create_index(op.f('ix_chat_members_auth_user_id'), 'chat_members', ['auth_user_id'], unique=False)
    op.create_index(op.f('ix_chat_members_chat_id'), 'chat_members', ['chat_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_chat_members_chat_id'), table_name='chat_members')
    op.drop_index(op.f('ix_chat_members_auth_user_id'), table_name='chat_members')
    op.drop_table('chat_members')
    op.drop_table('chats')
    sa.Enum(name='chattype').drop(op.get_bind(), checkfirst=True)
