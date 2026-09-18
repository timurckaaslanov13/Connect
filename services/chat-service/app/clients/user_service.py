import httpx

from app.core.config import settings


async def get_user_profile(
    auth_user_id: int,
) -> dict | None:
    url = (
        f"{settings.user_service_url}"
        f"/users/by-auth-id/{auth_user_id}"
    )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                timeout=3.0,
            )

        if response.status_code == 404:
            return None

        response.raise_for_status()

        return response.json()

    except httpx.HTTPError:
        return None