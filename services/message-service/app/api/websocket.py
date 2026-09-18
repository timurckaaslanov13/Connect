import asyncio
import logging
import time
from typing import Literal

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.exc import SQLAlchemyError
from starlette.websockets import WebSocketState

from app.clients.chat_service import ChatServiceUnavailable, check_user_chat_membership
from app.schemas.message import MessageCreate
from app.security.jwt import decode_access_token, get_access_token_expiry
from app.services.messages import create_message
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix='/ws', tags=['websocket'])
AUTH_TIMEOUT_SECONDS = 5


class SocketAuth(BaseModel):
    type: Literal['auth']
    token: str = Field(min_length=1, max_length=8192)


@router.websocket('/chats/{chat_id}')
async def chat_websocket(websocket: WebSocket, chat_id: int):
    # Credentials are sent in the first frame, never in a logged URL.
    await websocket.accept()
    try:
        async with asyncio.timeout(AUTH_TIMEOUT_SECONDS):
            credentials = SocketAuth.model_validate_json(await websocket.receive_text())
            user_id = decode_access_token(credentials.token)
            expires_at = get_access_token_expiry(credentials.token)
            if chat_id < 1 or not await check_user_chat_membership(chat_id, user_id):
                raise ValueError('Access denied')
    except WebSocketDisconnect:
        return
    except (ValueError, KeyError, TimeoutError):
        await websocket.close(code=1008)
        return
    except ChatServiceUnavailable:
        await websocket.close(code=1011)
        return

    await manager.connect(chat_id, websocket, accepted=True)
    try:
        await websocket.send_json({'type': 'ready', 'chat_id': chat_id})
        # Expiry closes idle sockets too, not just sockets that send messages.
        async with asyncio.timeout(max(0, expires_at - time.time())):
            while websocket.application_state == WebSocketState.CONNECTED:
                text = await websocket.receive_text()
                try:
                    data = MessageCreate(chat_id=chat_id, text=text)
                except ValidationError:
                    await websocket.send_json({'error': 'Сообщение должно содержать от 1 до 5000 символов и не состоять из пробелов'})
                    continue
                try:
                    await create_message(sender_id=user_id, data=data)
                except PermissionError:
                    await websocket.close(code=1008)
                    return
    except WebSocketDisconnect:
        pass
    except (TimeoutError, KeyError):
        await websocket.close(code=1008)
    except ChatServiceUnavailable:
        await websocket.close(code=1011)
    except SQLAlchemyError:
        logger.exception('Could not save WebSocket message')
        await websocket.close(code=1011)
    finally:
        manager.disconnect(chat_id, websocket)
