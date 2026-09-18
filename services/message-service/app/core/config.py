from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    internal_api_key: str = Field(min_length=32)
    database_url: str

    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"

    chat_service_url: str


settings = Settings()