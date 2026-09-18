import httpx

from app.core.config import settings


async def check_user_chat_membership(
    chat_id: int,
    user_id: int,
) -> bool:
    url = (
        f"{settings.chat_service_url}"
        f"/chats/{chat_id}/members/{user_id}/check"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                timeout=3.0,
            )

        response.raise_for_status()

        data = response.json()

        return data["is_member"]

    except httpx.HTTPError:
        return False