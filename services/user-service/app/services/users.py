from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.profile import Profile
from app.schemas.profile import ProfileCreate, ProfileUpdate


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

def get_profile(
    db: Session,
    auth_user_id: int,
) -> Profile | None:
    return db.scalar(
        select(Profile).where(
            Profile.auth_user_id == auth_user_id
        )
    )

def update_profile(
    db: Session,
    auth_user_id: int,
    data: ProfileUpdate,
) -> Profile:
    profile = get_profile(db, auth_user_id)

    if profile is None:
        raise ValueError("Профиль не найден")

    update_data = data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(profile)

    return profile

def get_profile_by_id(
    db: Session,
    profile_id: int,
) -> Profile | None:
    return db.get(Profile, profile_id)

def get_profile_by_auth_user_id(
    db: Session,
    auth_user_id: int,
) -> Profile | None:
    return db.scalar(
        select(Profile).where(
            Profile.auth_user_id == auth_user_id
        )
    )