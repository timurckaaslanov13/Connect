"""Run with: python -m unittest discover -s tests -p test_message_websocket.py"""
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-' * 8,
                  CHAT_SERVICE_URL='http://chat.test')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.api import websocket as endpoint
from app.database.connection import Base
from app.models.message import Message
from app.websocket.manager import manager


class WebSocketTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)
        self.client = TestClient(app)
        manager.active_connections.clear()

    def tearDown(self):
        self.client.close()
        self.engine.dispose()
        manager.active_connections.clear()

    def test_missing_token(self):
        with self.assertRaises(WebSocketDisconnect) as error:
            with self.client.websocket_connect('/ws/chats/1'):
                pass
        self.assertEqual(error.exception.code, 1008)

    def test_invalid_token(self):
        with self.assertRaises(WebSocketDisconnect) as error:
            with self.client.websocket_connect('/ws/chats/1?token=bad'):
                pass
        self.assertEqual(error.exception.code, 1008)

    def test_nonmember(self):
        with patch.object(endpoint, 'decode_access_token', return_value=7), patch.object(endpoint, 'check_user_chat_membership', AsyncMock(return_value=False)):
            with self.assertRaises(WebSocketDisconnect) as error:
                with self.client.websocket_connect('/ws/chats/1?token=test'):
                    pass
            self.assertEqual(error.exception.code, 1008)
        self.assertFalse(manager.active_connections)

    def test_delivery_validation_persistence_cleanup(self):
        with patch.object(endpoint, 'decode_access_token', return_value=7), patch.object(endpoint, 'check_user_chat_membership', AsyncMock(return_value=True)), patch.object(endpoint, 'SessionLocal', self.session):
            with self.client.websocket_connect('/ws/chats/1?token=test') as first:
                with self.client.websocket_connect('/ws/chats/1?token=test') as second:
                    first.send_text('x' * 5001)
                    self.assertIn('error', first.receive_json())
                    first.send_text('   ')
                    first.send_text('Привет')
                    result = first.receive_json()
                    self.assertEqual(second.receive_json(), result)
                    self.assertEqual(result['text'], 'Привет')
                    self.assertEqual(result['sender_id'], 7)
                    with self.session() as db:
                        self.assertEqual(len(db.scalars(select(Message)).all()), 1)
        self.assertFalse(manager.active_connections)


if __name__ == '__main__':
    unittest.main()
