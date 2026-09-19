from datetime import datetime
from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database.connection import Base


class Call(Base):
    __tablename__ = 'calls'
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    chat_id: Mapped[int] = mapped_column(index=True)
    caller_id: Mapped[int] = mapped_column(index=True)
    callee_id: Mapped[int] = mapped_column(index=True)
    media: Mapped[str] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(16), default='ringing')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
