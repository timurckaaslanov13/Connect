from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings
from jwt import ExpiredSignatureError, InvalidTokenError


def create_access_token(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token

def decode_access_token(token: str) -> int:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise InvalidTokenError()

        return int(user_id)

    except ExpiredSignatureError:
        raise ValueError("Срок действия токена истёк")

    except InvalidTokenError:
        raise ValueError("Недействительный токен")