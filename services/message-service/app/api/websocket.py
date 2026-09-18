import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.clients.chat_service import check_user_chat_membership
from app.schemas.message import MessageCreate
from app.security.jwt import decode_access_token
from app.services.messages import create_message
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/ws', tags=['websocket'])


@router.websocket('/chats/{chat_id}')
async def chat_websocket(websocket: WebSocket, chat_id: int):
    token = websocket.query_params.get('token')
    try:
        if not token or chat_id < 1:
            raise ValueError('Invalid credentials')
        user_id = decode_access_token(token)
    except ValueError:
        await websocket.close(code=1008)
        return

    if not await check_user_chat_membership(chat_id, user_id):
        await websocket.close(code=1008)
        return

    await manager.connect(chat_id, websocket)
    try:
        while True:
            text = await websocket.receive_text()
            try:
                data = MessageCreate(chat_id=chat_id, text=text)
            except ValidationError:
                await websocket.send_json({'error': 'Сообщение должно содержать от 1 до 5000 символов и не состоять из пробелов'})
                continue
            try:
                decode_access_token(token)
                await create_message(sender_id=user_id, data=data)
            except (ValueError, PermissionError):
                await websocket.close(code=1008)
                return
    except WebSocketDisconnect:
        pass
    except SQLAlchemyError:
        logger.exception('Could not save WebSocket message')
        await websocket.close(code=1011)
    finally:
        manager.disconnect(chat_id, websocket)
