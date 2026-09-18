from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
 

from app.database.dependencies import get_db

from app.security.dependencies import get_current_user_id
from app.schemas.profile import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)

from app.services.users import (
    create_profile,
    get_profile,
    update_profile,
    search_profiles,
    get_profile_by_id,
    get_profile_by_auth_user_id
)

router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.post(
    "/profile",
    response_model=ProfileResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_profile(
    data: ProfileCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        return create_profile(
            db=db,
            auth_user_id=user_id,
            data=data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

@router.get(
    "/profile",
    response_model=ProfileResponse,
)
def get_user_profile(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    profile = get_profile(db, user_id)

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден",
        )

    return profile


@router.patch(
    "/profile",
    response_model=ProfileResponse,
)
def update_user_profile(
    data: ProfileUpdate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        return update_profile(
            db=db,
            auth_user_id=user_id,
            data=data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
        
@router.get(
    "/search",
    response_model=list[ProfileResponse],
)
def search_users(
    user_id: int = Depends(get_current_user_id),
    q: str = Query(
        min_length=2,
        max_length=100,
    ),
    db: Session = Depends(get_db),
):
    return search_profiles(
        db=db,
        query=q,
    )
    
@router.get(
    "/{profile_id}",
    response_model=ProfileResponse,
)
def get_user_by_id(
    profile_id: int,
    db: Session = Depends(get_db),
):
    profile = get_profile_by_id(
        db=db,
        profile_id=profile_id,
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден",
        )

    return profile

@router.get(
    "/by-auth-id/{auth_user_id}",
    response_model=ProfileResponse,
)
def get_user_by_auth_id(
    auth_user_id: int,
    db: Session = Depends(get_db),
):
    profile = get_profile_by_auth_user_id(
        db=db,
        auth_user_id=auth_user_id,
    )

    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Профиль не найден",
        )

    return profile