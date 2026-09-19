from pydantic import BaseModel, Field


class ProfileCreate(BaseModel):
    display_name: str = Field(min_length=2, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None


class ProfileResponse(BaseModel):
    username: str | None = None
    id: int
    auth_user_id: int
    display_name: str
    bio: str | None
    avatar_url: str | None

    model_config = {
        "from_attributes": True
    }

class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=2, max_length=100)
    bio: str | None = Field(default=None, max_length=500)
    avatar_url: str | None = None