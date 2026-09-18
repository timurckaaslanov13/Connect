from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.schemas.message import MessageCreate

from app.clients.chat_service import check_user_chat_membership
from app.database.connection import SessionLocal
from app.models.message import Message
from app.security.jwt import decode_access_token
from app.websocket.manager import manager


router = APIRouter(
    prefix="/ws",
    tags=["websocket"],
)


@router.websocket("/chats/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: int,
):
    token = websocket.query_params.get("token")

    if token is None:
        await websocket.close(code=1008)
        return

    try:
        user_id = decode_access_token(token)

    except ValueError:
        await websocket.close(code=1008)
        return

    is_member = await check_user_chat_membership(
        chat_id=chat_id,
        user_id=user_id,
    )

    if not is_member:
        await websocket.close(code=1008)
        return

    await manager.connect(
        chat_id=chat_id,
        websocket=websocket,
    )

    db = SessionLocal()

    try:
        while True:
            text = await websocket.receive_text()

            if not text.strip():
                continue

            try:
                MessageCreate(chat_id=chat_id, text=text)
            except ValidationError:
                await websocket.send_json({"error": "Сообщение должно содержать от 1 до 5000 символов"})
                continue

            message = Message(
                chat_id=chat_id,
                sender_id=user_id,
                text=text,
            )

            db.add(message)
            db.commit()
            db.refresh(message)

            await manager.broadcast(
                chat_id=chat_id,
                data={
                    "id": message.id,
                    "chat_id": message.chat_id,
                    "sender_id": message.sender_id,
                    "text": message.text,
                    "created_at": message.created_at.isoformat(),
                    "is_read": message.is_read,
                },
            )

    except WebSocketDisconnect:
        pass

    finally:
        manager.disconnect(
            chat_id=chat_id,
            websocket=websocket,
        )

        db.close()