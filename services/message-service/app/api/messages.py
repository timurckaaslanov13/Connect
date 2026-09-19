from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.clients.chat_service import ChatServiceUnavailable
from app.schemas.message import MessageCreate, MessageResponse
from app.security.dependencies import get_current_user_id
from app.services.messages import create_message, get_chat_messages

router = APIRouter(prefix='/messages', tags=['messages'])


@router.post('', response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(data: MessageCreate, user_id: int = Depends(get_current_user_id)):
    try:
        return await create_message(sender_id=user_id, data=data)
    except ChatServiceUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.get('/chat/{chat_id}', response_model=list[MessageResponse])
async def get_messages(
    chat_id: int,
    user_id: int = Depends(get_current_user_id),
    after_id: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    latest: bool = False,
    before_id: int | None = Query(default=None, gt=0),
):
    try:
        return await get_chat_messages(chat_id=chat_id, user_id=user_id, after_id=after_id, limit=limit, latest=latest, before_id=before_id)
    except ChatServiceUnavailable as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.get('/inbox')
async def inbox(user_id: int = Depends(get_current_user_id)):
    from app.clients.chat_service import get_user_chat_ids
    from app.services.inbox import load_inbox
    from fastapi.concurrency import run_in_threadpool
    try:
        ids = await get_user_chat_ids(user_id)
        return await run_in_threadpool(load_inbox, ids, user_id)
    except ChatServiceUnavailable as error:
        raise HTTPException(503, str(error)) from error


@router.post('/chat/{chat_id}/read')
async def read_chat(chat_id: int, user_id: int = Depends(get_current_user_id)):
    from app.clients.chat_service import check_user_chat_membership, get_chat_members
    from app.services.inbox import mark_read
    from app.websocket.user_events import user_events
    from fastapi.concurrency import run_in_threadpool
    try:
        if not await check_user_chat_membership(chat_id, user_id):
            raise HTTPException(403, 'Нет доступа к чату')
        last_id = await run_in_threadpool(mark_read, chat_id, user_id)
        for member in await get_chat_members(chat_id):
            try:
                await user_events.send(member, {'type':'read', 'chat_id':chat_id, 'user_id':user_id, 'last_id':last_id})
            except Exception:
                pass
        return {'last_id': last_id}
    except ChatServiceUnavailable as error:
        raise HTTPException(503, str(error)) from error
