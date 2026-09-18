import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-' * 8,
                  INTERNAL_API_KEY='test-internal-key-' * 4, CHAT_SERVICE_URL='http://chat.test')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import httpx
from app.clients import chat_service
from app.core.config import settings


class MembershipClientTests(unittest.IsolatedAsyncioTestCase):
    async def check_response(self, response):
        def handle(request):
            self.assertEqual(request.headers['X-Internal-Token'], settings.internal_api_key)
            return response
        client = httpx.AsyncClient(transport=httpx.MockTransport(handle))
        with patch.object(chat_service.httpx, 'AsyncClient', return_value=client):
            return await chat_service.check_user_chat_membership(1, 7)

    async def test_real_denial(self):
        self.assertFalse(await self.check_response(httpx.Response(200, json={'is_member': False})))

    async def test_bad_upstream_is_unavailable(self):
        for response in [httpx.Response(500), httpx.Response(401), httpx.Response(200, json={'is_member': 'false'}), httpx.Response(200, text='bad JSON')]:
            with self.assertRaises(chat_service.ChatServiceUnavailable):
                await self.check_response(response)
