from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.chat import Chat, ChatType
from app.models.chat_member import ChatMember


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