from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.message import MessageCreate, MessageResponse
from app.security.dependencies import get_current_user_id
from app.services.messages import create_message, get_chat_messages

router = APIRouter(prefix='/messages', tags=['messages'])


@router.post('', response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(data: MessageCreate, user_id: int = Depends(get_current_user_id)):
    try:
        return await create_message(sender_id=user_id, data=data)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error


@router.get('/chat/{chat_id}', response_model=list[MessageResponse])
async def get_messages(chat_id: int, user_id: int = Depends(get_current_user_id)):
    try:
        return await get_chat_messages(chat_id=chat_id, user_id=user_id)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
