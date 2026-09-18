"""Run separately: python -m unittest discover -s tests -p test_chat_list.py"""
import os
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-' * 8,
                  USER_SERVICE_URL='http://user.test')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services import chats


class ChatListTests(unittest.IsolatedAsyncioTestCase):
    async def test_empty_list(self):
        with patch.object(chats, 'get_user_chats', return_value=[]):
            self.assertEqual(await chats.get_user_private_chats(Mock(), 1), [])

    async def test_all_chats_and_missing_member(self):
        rows = [SimpleNamespace(id=i, type='private', created_at=None) for i in (1, 2, 3)]
        db = Mock()
        db.scalar.side_effect = [SimpleNamespace(auth_user_id=10), None, SimpleNamespace(auth_user_id=20)]
        with patch.object(chats, 'get_user_chats', return_value=rows), patch.object(chats, 'get_user_profile', AsyncMock(return_value=None)):
            result = await chats.get_user_private_chats(db, 1)
        self.assertEqual([item['id'] for item in result], [1, 3])
        self.assertEqual([item['other_user_id'] for item in result], [10, 20])


if __name__ == '__main__':
    unittest.main()
