from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserRegister
from app.exceptions.auth import UserAlreadyExistsError

password_hash = PasswordHash.recommended()



def register_user(db: Session, data: UserRegister) -> User:
    existing_user = db.scalar(
        select(User).where(
            (User.email == data.email) |
            (User.username == data.username)
        )
    )

    if existing_user:
        raise UserAlreadyExistsError("Пользователь уже существует")

    hashed_password = password_hash.hash(data.password)

    user = User(
        email=data.email,
        username=data.username,
        password_hash=hashed_password,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user