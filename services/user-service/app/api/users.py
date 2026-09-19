from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
 

from app.database.dependencies import get_db

from app.security.dependencies import get_current_user_id, bearer_scheme
from app.schemas.profile import (
    ProfileCreate,
    ProfileResponse,
    ProfileUpdate,
)

from app.services.users import (
    create_profile,
    get_profile,
    update_profile,
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
    credentials = Depends(bearer_scheme),
    user_id: int = Depends(get_current_user_id),
    q: str = Query(
        min_length=2,
        max_length=100,
    ),
    db: Session = Depends(get_db),
):
    import json
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode
    from urllib.error import URLError
    from sqlalchemy import select
    from app.models.profile import Profile
    from app.core.config import settings
    try:
        request = Request(settings.auth_service_url + '/auth/directory?' + urlencode({'q': q}), headers={'Authorization': 'Bearer ' + credentials.credentials})
        with urlopen(request, timeout=5) as response:
            users = json.load(response)
    except (URLError, TimeoutError, ValueError):
        raise HTTPException(503, 'Поиск временно недоступен') from None
    profiles = {p.auth_user_id: p for p in db.scalars(select(Profile).where(Profile.auth_user_id.in_([u['auth_user_id'] for u in users])))}
    return [ProfileResponse.model_validate(profiles[u['auth_user_id']]).model_copy(update={'username': u['username']}) for u in users if u['auth_user_id'] in profiles]
    
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