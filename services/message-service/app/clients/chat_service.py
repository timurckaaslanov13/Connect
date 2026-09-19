import httpx
from app.core.config import settings


class ChatServiceUnavailable(Exception):
    pass


async def check_user_chat_membership(chat_id: int, user_id: int) -> bool:
    url = f'{settings.chat_service_url}/chats/{chat_id}/members/{user_id}/check'
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={'X-Internal-Token': settings.internal_api_key}, timeout=3.0)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict) or type(data.get('is_member')) is not bool:
            raise ValueError('Invalid membership response')
        return data['is_member']
    except (httpx.HTTPError, ValueError) as error:
        raise ChatServiceUnavailable('Сервис чатов временно недоступен') from error


async def get_chat_members(chat_id: int) -> list[int]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{settings.chat_service_url}/chats/{chat_id}/members', headers={'X-Internal-Token': settings.internal_api_key}, timeout=3)
        response.raise_for_status()
        members = response.json()['members']
        if not isinstance(members, list) or not all(type(user) is int for user in members):
            raise ValueError('Invalid members')
        return members
    except (httpx.HTTPError, ValueError, KeyError) as error:
        raise ChatServiceUnavailable('Сервис чатов временно недоступен') from error


async def get_user_chat_ids(user_id: int) -> list[int]:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f'{settings.chat_service_url}/chats/internal/users/{user_id}/chats', headers={'X-Internal-Token': settings.internal_api_key}, timeout=3)
        response.raise_for_status()
        ids = response.json()['chats']
        if not isinstance(ids, list) or not all(type(chat) is int for chat in ids):
            raise ValueError('Invalid chats')
        return ids
    except (httpx.HTTPError, ValueError, KeyError) as error:
        raise ChatServiceUnavailable('Сервис чатов временно недоступен') from error
