from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.exceptions.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.models.user import User
from app.security.dependencies import get_current_user

from app.schemas.user import (
    TokenResponse,
    UserLogin,
    UserRegister,
    UserResponse,
)

from app.services.auth import (
    login_user,
    register_user,
)
from app.security.jwt import create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db),
):
    try:
        return register_user(db, data)

    except UserAlreadyExistsError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    try:
        user = login_user(db, data)

        token = create_access_token(user.id)

        return TokenResponse(
            access_token=token,
        )

    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )
        
@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(get_current_user),
):
    return current_user

@router.get('/directory')
def directory(q: str = Query(min_length=2, max_length=50), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    from sqlalchemy import select, func
    query = q.strip().lstrip('@').lower()
    if len(query) < 2:
        return []
    rows = db.scalars(select(User).where(func.lower(User.username).startswith(query, autoescape=True)).order_by(User.username, User.id).limit(20))
    return [{'auth_user_id': row.id, 'username': row.username} for row in rows]


@router.get('/directory/{user_id}')
def public_account(user_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(404, 'Пользователь не найден')
    return {'auth_user_id': user.id, 'username': user.username}
