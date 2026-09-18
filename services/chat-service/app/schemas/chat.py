from datetime import datetime

from pydantic import BaseModel, Field


class PrivateChatCreate(BaseModel):
    other_user_id: int = Field(gt=0)


class ChatResponse(BaseModel):
    id: int
    type: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }

class PrivateChatResponse(BaseModel):
    id: int
    type: str
    other_user_id: int
    other_user_name: str | None
    other_user_avatar_url: str | None
    created_at: datetime