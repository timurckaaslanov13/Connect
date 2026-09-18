from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class MessageCreate(BaseModel):
    chat_id: int = Field(gt=0)
    text: str = Field(
        min_length=1,
        max_length=5000,
    )


    @field_validator("text")
    @classmethod
    def reject_whitespace(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Сообщение не может состоять из пробелов")
        return value


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