from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select

from app.clients.chat_service import check_user_chat_membership, get_chat_members
from app.websocket.user_events import user_events
import logging
from app.database.connection import SessionLocal
from app.models.message import Message
from app.schemas.message import MessageCreate, MessageResponse
from app.websocket.events import events


def _save_message(sender_id: int, data: MessageCreate) -> MessageResponse:
    # The whole session lives in one worker thread and ends before broadcasting.
    with SessionLocal() as db:
        message = Message(chat_id=data.chat_id, sender_id=sender_id, text=data.text)
        db.add(message)
        db.commit()
        db.refresh(message)
        return MessageResponse.model_validate(message)


async def create_message(sender_id: int, data: MessageCreate) -> MessageResponse:
    if not await check_user_chat_membership(data.chat_id, sender_id):
        raise PermissionError('Пользователь не состоит в этом чате')
    message = await run_in_threadpool(_save_message, sender_id, data)
    await events.publish(data.chat_id, message.model_dump(mode='json'))
    if user_events.redis:
        try:
            for member in await get_chat_members(data.chat_id):
                await user_events.send(member, {'type': 'message', 'message': message.model_dump(mode='json')})
        except Exception:
            logging.getLogger(__name__).warning('Saved message notification unavailable')
    return message


def _load_messages(chat_id: int, after_id: int, limit: int, latest: bool, before_id: int | None) -> list[MessageResponse]:
    with SessionLocal() as db:
        statement = (
            select(Message)
            .where(Message.chat_id == chat_id, Message.id > after_id)
            .order_by(Message.id.desc() if latest else Message.id.asc())
            .limit(limit)
        )
        if before_id is not None:
            statement = statement.where(Message.id < before_id)
        rows = [MessageResponse.model_validate(message) for message in db.scalars(statement)]
        return list(reversed(rows)) if latest else rows


async def get_chat_messages(chat_id: int, user_id: int, after_id: int = 0, limit: int = 50, latest: bool = False, before_id: int | None = None) -> list[MessageResponse]:
    if not await check_user_chat_membership(chat_id, user_id):
        raise PermissionError('Пользователь не состоит в этом чате')
    return await run_in_threadpool(_load_messages, chat_id, after_id, limit, latest, before_id)
