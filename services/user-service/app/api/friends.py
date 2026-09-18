from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.database.dependencies import get_db
from app.models.friendship import Friendship
from app.models.profile import Profile
from app.security.dependencies import get_current_user_id

router = APIRouter(prefix='/friends', tags=['friends'])


class FriendRequest(BaseModel):
    user_id: int = Field(gt=0)


def serialize(row, user_id, profile):
    return dict(id=row.id, status=row.status,
                direction='outgoing' if row.requester_id == user_id else 'incoming',
                user_id=profile.auth_user_id, display_name=profile.display_name,
                avatar_url=profile.avatar_url, bio=profile.bio)


@router.get('')
def list_friends(user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    rows = db.scalars(select(Friendship).where(or_(Friendship.requester_id == user_id, Friendship.recipient_id == user_id)).order_by(Friendship.id.desc())).all()
    ids = [r.recipient_id if r.requester_id == user_id else r.requester_id for r in rows]
    profiles = {p.auth_user_id: p for p in db.scalars(select(Profile).where(Profile.auth_user_id.in_(ids)))}
    return [serialize(r, user_id, profiles[other]) for r, other in zip(rows, ids) if other in profiles]


@router.post('/requests', status_code=201)
def request_friend(data: FriendRequest, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    if data.user_id == user_id:
        raise HTTPException(400, 'Нельзя добавить себя в друзья')
    profiles = db.scalars(select(Profile).where(Profile.auth_user_id.in_([user_id, data.user_id]))).all()
    if len(profiles) != 2:
        raise HTTPException(404, 'Профиль пользователя не найден')
    key = ':'.join(map(str, sorted([user_id, data.user_id])))
    row = db.scalar(select(Friendship).where(Friendship.pair_key == key))
    if row is None:
        row = Friendship(pair_key=key, requester_id=user_id, recipient_id=data.user_id)
        db.add(row)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            row = db.scalar(select(Friendship).where(Friendship.pair_key == key))
            if row is None:
                raise
    return {'id': row.id, 'status': row.status}


@router.post('/requests/{request_id}/accept')
def accept_friend(request_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    row = db.get(Friendship, request_id)
    if row is None or row.recipient_id != user_id:
        raise HTTPException(404, 'Заявка не найдена')
    row.status = 'accepted'
    db.commit()
    return {'id': row.id, 'status': row.status}


@router.delete('/{request_id}', status_code=204)
def remove_friend(request_id: int, user_id: int = Depends(get_current_user_id), db: Session = Depends(get_db)):
    row = db.get(Friendship, request_id)
    if row is None or user_id not in (row.requester_id, row.recipient_id):
        raise HTTPException(404, 'Заявка не найдена')
    db.delete(row)
    db.commit()
