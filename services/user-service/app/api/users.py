from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.profile import ProfileCreate, ProfileResponse
from app.security.dependencies import get_current_user_id
from app.services.users import create_profile


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