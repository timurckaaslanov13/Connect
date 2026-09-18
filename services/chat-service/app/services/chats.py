from sqlalchemy import func, select
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
        raise ValueError("Нельзя создать чат с самим собой")

    existing_chat = db.scalar(
        select(Chat)
        .join(ChatMember)
        .where(
            Chat.type == ChatType.PRIVATE,
            Chat.id.in_(
                select(ChatMember.chat_id)
                .where(
                    ChatMember.auth_user_id.in_(
                        [current_user_id, other_user_id]
                    )
                )
                .group_by(ChatMember.chat_id)
                .having(
                    func.count(ChatMember.id) == 2
                )
            )
        )
    )

    if existing_chat:
        return existing_chat

    chat = Chat(
        type=ChatType.PRIVATE,
    )

    db.add(chat)
    db.flush()

    first_member = ChatMember(
        chat_id=chat.id,
        auth_user_id=current_user_id,
    )

    second_member = ChatMember(
        chat_id=chat.id,
        auth_user_id=other_user_id,
    )

    db.add_all([
        first_member,
        second_member,
    ])

    db.commit()
    db.refresh(chat)

    return chat

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

