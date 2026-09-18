from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    jwt_secret_key: str = Field(min_length=32)
    jwt_algorithm: str = "HS256"

settings = Settings()