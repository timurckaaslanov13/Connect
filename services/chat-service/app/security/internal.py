from secrets import compare_digest

from fastapi import Header, HTTPException
from app.core.config import settings


def require_internal_key(x_internal_token: str | None = Header(default=None)) -> None:
    if x_internal_token is None or not compare_digest(x_internal_token.encode('utf-8'), settings.internal_api_key.encode('utf-8')):
        raise HTTPException(status_code=401, detail='Invalid service credentials')
