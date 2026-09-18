import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-' * 8,
                  INTERNAL_API_KEY='test-internal-key-' * 4, USER_SERVICE_URL='http://user.test')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings


class InternalAccessTests(unittest.TestCase):
    def test_membership_requires_service_key(self):
        with TestClient(app) as client, patch('app.api.chats.is_user_chat_member', return_value=True):
            url = '/chats/1/members/7/check'
            self.assertEqual(client.get(url).status_code, 401)
            self.assertEqual(client.get(url, headers={'X-Internal-Token': 'wrong'}).status_code, 401)
            response = client.get(url, headers={'X-Internal-Token': settings.internal_api_key})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {'is_member': True})
