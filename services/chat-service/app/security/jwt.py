import math
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError

from app.core.config import settings


def _decode_claims(token: str) -> dict:
    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm],
            options={"require": ["sub", "exp"]},
        )
        subject = payload["sub"]
        expiry = payload["exp"]
        if not isinstance(subject, str) or not subject.isascii() or not subject.isdecimal() or int(subject) < 1:
            raise InvalidTokenError("Invalid subject")
        if isinstance(expiry, bool) or not isinstance(expiry, (int, float)) or not math.isfinite(expiry):
            raise InvalidTokenError("Invalid expiry")
        return payload
    except ExpiredSignatureError as error:
        raise ValueError("Срок действия токена истёк") from error
    except (InvalidTokenError, ValueError, TypeError, OverflowError) as error:
        raise ValueError("Недействительный токен") from error


def decode_access_token(token: str) -> int:
    return int(_decode_claims(token)["sub"])


def get_access_token_expiry(token: str) -> float:
    return float(_decode_claims(token)["exp"])
