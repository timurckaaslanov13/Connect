from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.dependencies import get_db
from app.schemas.chat import ChatResponse, PrivateChatCreate
from app.security.dependencies import get_current_user_id
from app.services.chats import create_private_chat


router = APIRouter(
    prefix="/chats",
    tags=["chats"],
)


@router.post(
    "/private",
    response_model=ChatResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_private_chat_endpoint(
    data: PrivateChatCreate,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    try:
        return create_private_chat(
            db=db,
            current_user_id=user_id,
            other_user_id=data.other_user_id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )