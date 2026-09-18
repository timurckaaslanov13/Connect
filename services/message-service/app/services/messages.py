from sqlalchemy.orm import Session

from app.clients.chat_service import check_user_chat_membership
from app.models.message import Message
from app.schemas.message import MessageCreate
from sqlalchemy import select

async def create_message(
    db: Session,
    sender_id: int,
    data: MessageCreate,
) -> Message:
    is_member = await check_user_chat_membership(
        chat_id=data.chat_id,
        user_id=sender_id,
    )

    if not is_member:
        raise ValueError(
            "Пользователь не состоит в этом чате"
        )

    message = Message(
        chat_id=data.chat_id,
        sender_id=sender_id,
        text=data.text,
    )

    db.add(message)
    db.commit()
    db.refresh(message)

    return message


async def get_chat_messages(
    db: Session,
    chat_id: int,
    user_id: int,
) -> list[Message]:
    is_member = await check_user_chat_membership(
        chat_id=chat_id,
        user_id=user_id,
    )

    if not is_member:
        raise ValueError(
            "Пользователь не состоит в этом чате"
        )

    statement = (
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at.asc())
    )

    return list(
        db.scalars(statement).all()
    )