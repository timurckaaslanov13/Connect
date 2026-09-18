import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

os.environ.update(DATABASE_URL='sqlite://', JWT_SECRET_KEY='test-key-' * 8,
                  INTERNAL_API_KEY='test-internal-key-' * 4, CHAT_SERVICE_URL='http://chat.test')
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from redis.exceptions import ConnectionError
from app.websocket import events as event_module
from app.websocket.events import MessageEvents
from app.websocket.manager import ConnectionManager


class EventTests(unittest.IsolatedAsyncioTestCase):
    async def test_local_delivery(self):
        bus = MessageEvents(None)
        with patch.object(event_module.manager, 'broadcast', AsyncMock()) as broadcast:
            await bus.publish(1, {'id': 5})
            broadcast.assert_awaited_once_with(1, {'id': 5})

    async def test_redis_delivery_is_not_also_broadcast_locally(self):
        bus = MessageEvents('redis://example')
        bus.redis = AsyncMock()
        bus.ready = True
        with patch.object(event_module.manager, 'broadcast', AsyncMock()) as broadcast:
            await bus.publish(1, {'id': 5})
            bus.redis.publish.assert_awaited_once()
            broadcast.assert_not_awaited()

    async def test_publish_failure_preserves_success_and_closes_sockets(self):
        bus = MessageEvents('redis://example')
        bus.redis = AsyncMock()
        bus.redis.publish.side_effect = ConnectionError('offline')
        bus.ready = True
        with patch.object(event_module.manager, 'close_all', AsyncMock()) as close:
            await bus.publish(1, {'id': 5})
            close.assert_awaited_once()

    async def test_failed_socket_does_not_break_other_recipient(self):
        manager = ConnectionManager()
        bad, good = AsyncMock(), AsyncMock()
        bad.send_json.side_effect = RuntimeError('closed')
        await manager.connect(1, bad)
        await manager.connect(1, good)
        await manager.broadcast(1, {'id': 5})
        good.send_json.assert_awaited_once_with({'id': 5})
        self.assertEqual(manager.active_connections[1], [good])
        await manager.close_all()
        self.assertEqual(manager.active_connections, {})
        self.assertEqual(manager._send_locks, {})
