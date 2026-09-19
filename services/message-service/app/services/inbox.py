from sqlalchemy import select, func, update
from app.database.connection import SessionLocal
from app.models.message import Message
from app.schemas.message import MessageResponse


def load_inbox(chat_ids, user_id):
    if not chat_ids: return []
    with SessionLocal() as db:
        latest = select(func.max(Message.id)).where(Message.chat_id.in_(chat_ids)).group_by(Message.chat_id)
        messages = {m.chat_id: MessageResponse.model_validate(m).model_dump(mode='json') for m in db.scalars(select(Message).where(Message.id.in_(latest)))}
        unread = dict(db.execute(select(Message.chat_id, func.count(Message.id)).where(Message.chat_id.in_(chat_ids), Message.sender_id != user_id, Message.is_read.is_(False)).group_by(Message.chat_id)).all())
        return [{'chat_id': i, 'last_message': messages.get(i), 'unread': unread.get(i,0)} for i in chat_ids]


def mark_read(chat_id, user_id):
    with SessionLocal() as db:
        last = db.scalar(select(func.max(Message.id)).where(Message.chat_id==chat_id, Message.sender_id != user_id))
        if last:
            db.execute(update(Message).where(Message.chat_id==chat_id, Message.sender_id != user_id, Message.id<=last).values(is_read=True))
            db.commit()
        return last or 0
