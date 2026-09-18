from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.chat import Chat, ChatType
from app.models.chat_member import ChatMember
from app.clients.user_service import get_user_profile


def create_private_chat(
    db: Session,
    current_user_id: int,
    other_user_id: int,
) -> Chat:
    if current_user_id == other_user_id:
        raise ValueError("РќРµР»СЊР·СЏ СЃРѕР·РґР°С‚СЊ С‡Р°С‚ СЃ СЃР°РјРёРј СЃРѕР±РѕР№")

    private_key = ":".join(str(user_id) for user_id in sorted((current_user_id, other_user_id)))
    existing_chat = db.scalar(select(Chat).where(Chat.private_key == private_key))
    if existing_chat:
        return existing_chat

    chat = Chat(type=ChatType.PRIVATE, private_key=private_key)
    try:
        db.add(chat)
        db.flush()
        db.add_all([
            ChatMember(chat_id=chat.id, auth_user_id=current_user_id),
            ChatMember(chat_id=chat.id, auth_user_id=other_user_id),
        ])
        db.commit()
        db.refresh(chat)
        return chat
    except IntegrityError:
        db.rollback()
        # Another request may have committed the same pair while we inserted.
        existing_chat = db.scalar(select(Chat).where(Chat.private_key == private_key))
        if existing_chat is None:
            raise
        return existing_chat


def get_user_chats(
    db: Session,
    current_user_id: int,
) -> list[Chat]:
    statement = (
        select(Chat)
        .join(
            ChatMember,
            Chat.id == ChatMember.chat_id,
        )
        .where(
            ChatMember.auth_user_id == current_user_id
        )
        .order_by(Chat.created_at.desc())
    )

    return list(
        db.scalars(statement).all()
    )

async def get_user_private_chats(
    db: Session,
    current_user_id: int,
) -> list[dict]:
    chats = get_user_chats(
        db=db,
        current_user_id=current_user_id,
    )

    result = []

    for chat in chats:
        other_member = db.scalar(
            select(ChatMember)
            .where(
                ChatMember.chat_id == chat.id,
                ChatMember.auth_user_id != current_user_id,
            )
        )

        if other_member is None:
            continue
        profile = await get_user_profile(
            other_member.auth_user_id
        )

        result.append(
            {
                "id": chat.id,
                "type": chat.type,
                "other_user_id": other_member.auth_user_id,
                "other_user_name": (
                    profile["display_name"]
                    if profile
                    else None
                ),
                "other_user_avatar_url": (
                    profile["avatar_url"]
                    if profile
                    else None
                ),
                "created_at": chat.created_at,
            }
        )

    return result

def is_user_chat_member(
    db: Session,
    chat_id: int,
    user_id: int,
) -> bool:
    member = db.scalar(
        select(ChatMember).where(
            ChatMember.chat_id == chat_id,
            ChatMember.auth_user_id == user_id,
        )
    )

    return member is not None
