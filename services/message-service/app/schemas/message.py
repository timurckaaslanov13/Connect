from datetime import datetime

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    chat_id: int
    text: str = Field(
        min_length=1,
        max_length=5000,
    )


class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    text: str
    created_at: datetime
    is_read: bool

    model_config = {
        "from_attributes": True
    }