from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.exceptions.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)

from app.schemas.user import (
    UserLogin,
    UserRegister,
    UserResponse,
)

from app.services.auth import (
    login_user,
    register_user,
)


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
    response_model=UserResponse,
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db),
):
    try:
        return login_user(db, data)

    except InvalidCredentialsError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
        )