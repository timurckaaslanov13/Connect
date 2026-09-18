from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SqlEnum, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.connection import Base


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"


class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(
        primary_key=True
    )

    type: Mapped[ChatType] = mapped_column(
        SqlEnum(ChatType),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )