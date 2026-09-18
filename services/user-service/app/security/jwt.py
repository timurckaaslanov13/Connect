import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


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