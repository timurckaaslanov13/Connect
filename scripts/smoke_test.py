"""Create disposable test accounts and check the live Connect stack.

Run against an isolated stack: python scripts/smoke_test.py --base-port 18000
Requires httpx and websockets from message-service requirements.
"""
import argparse
import asyncio
import secrets
import uuid

import httpx
from websockets.asyncio.client import connect
from websockets.exceptions import InvalidStatus


async def check(base_port):
    urls = [f'http://127.0.0.1:{base_port+i}' for i in range(4)]
    auth, users, chats, messages = urls
    with httpx.Client(timeout=10) as client:
        def request(method, url, token=None, **kwargs):
            headers = {'Authorization': f'Bearer {token}'} if token else {}
            response = client.request(method, url, headers=headers, **kwargs)
            response.raise_for_status()
            return response.json()

        for url in urls:
            request('GET', url + '/health')
        accounts = []
        suffix = uuid.uuid4().hex[:12]
        for i in range(3):
            email = f'smoke_{suffix}_{i}@example.com'
            password = secrets.token_urlsafe(24)
            user = request('POST', auth + '/auth/register', json={
                'email': email, 'username': f'smoke_{suffix}_{i}', 'password': password})
            token = request('POST', auth + '/auth/login', json={
                'email': email, 'password': password})['access_token']
            request('POST', users + '/users/profile', token, json={'display_name': f'Test user {i}'})
            accounts.append((user['id'], token))
        (first_id, first), (second_id, second), (_, outsider) = accounts
        assert request('GET', chats + '/chats', first) == []
        chat = request('POST', chats + '/chats/private', first, json={'other_user_id': second_id})
        chat_id = chat['id']
        duplicate = request('POST', chats + '/chats/private', second, json={'other_user_id': first_id})
        assert duplicate['id'] == chat_id
        listing = request('GET', chats + '/chats', first)
        assert listing[0]['other_user_name'] == 'Test user 1'
        forbidden = client.get(messages + f'/messages/chat/{chat_id}', headers={'Authorization': f'Bearer {outsider}'})
        assert forbidden.status_code == 403
        ws_url = f'ws://127.0.0.1:{base_port+3}/ws/chats/{chat_id}'
        for denied_token in ('invalid', outsider):
            try:
                async with connect(ws_url + '?token=' + denied_token):
                    raise AssertionError('Unauthorized WebSocket accepted')
            except InvalidStatus as error:
                assert error.response.status_code == 403
        async with connect(ws_url + '?token=' + first) as left, connect(ws_url + '?token=' + second) as right:
            await left.send('Привет из сквозного теста')
            sent, received = await asyncio.wait_for(asyncio.gather(left.recv(), right.recv()), 5)
            assert sent == received
        history = request('GET', messages + f'/messages/chat/{chat_id}', second)
        assert len(history) == 1 and history[0]['sender_id'] == first_id
        assert history[0]['text'] == 'Привет из сквозного теста'
        request('POST', messages + '/messages', second, json={'chat_id': chat_id, 'text': 'HTTP reply'})
        assert len(request('GET', messages + f'/messages/chat/{chat_id}', first)) == 2
    print('PASS: register, login, profiles, private chat, duplicate lookup, permissions, WebSocket delivery, HTTP send and history')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-port', type=int, default=18000)
    args = parser.parse_args()
    asyncio.run(check(args.base_port))
