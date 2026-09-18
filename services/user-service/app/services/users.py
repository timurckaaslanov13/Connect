from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate


def create_profile(
    db: Session,
    auth_user_id: int,
    data: ProfileCreate,
) -> Profile:
    existing_profile = db.scalar(
        select(Profile).where(
            Profile.auth_user_id == auth_user_id
        )
    )

    if existing_profile:
        raise ValueError("Профиль уже существует")

    profile = Profile(
        auth_user_id=auth_user_id,
        display_name=data.display_name,
        bio=data.bio,
        avatar_url=data.avatar_url,
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile