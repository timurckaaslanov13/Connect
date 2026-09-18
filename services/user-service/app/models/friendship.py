from datetime import datetime
from sqlalchemy import CheckConstraint, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.connection import Base


class Friendship(Base):
    __tablename__ = 'friendships'
    __table_args__ = (
        UniqueConstraint('pair_key', name='uq_friendship_pair'),
        CheckConstraint('requester_id != recipient_id', name='ck_friendship_distinct'),
        CheckConstraint("status IN ('pending', 'accepted')", name='ck_friendship_status'),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    pair_key: Mapped[str] = mapped_column(String(50))
    requester_id: Mapped[int] = mapped_column(Integer, index=True)
    recipient_id: Mapped[int] = mapped_column(Integer, index=True)
    status: Mapped[str] = mapped_column(String(16), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
