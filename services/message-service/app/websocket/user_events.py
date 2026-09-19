import asyncio
from contextlib import suppress
import json
import logging
from redis.asyncio import Redis
from redis.exceptions import RedisError
from app.core.config import settings
from app.websocket.manager import ConnectionManager

user_connections = ConnectionManager()
logger = logging.getLogger(__name__)


class UserEvents:
    def __init__(self):
        self.redis = None
        self.task = None
        self.ready = False

    async def start(self):
        if not settings.redis_url:
            return
        self.redis = Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=3)
        self.started = asyncio.Event()
        self.task = asyncio.create_task(self.listen())
        await asyncio.wait_for(self.started.wait(), 15)

    async def stop(self):
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
        await user_connections.close_all()
        if self.redis:
            await self.redis.aclose()
        self.ready = False

    async def listen(self):
        while True:
            try:
                async with self.redis.pubsub() as subscriber:
                    await subscriber.subscribe('connect:users')
                    while True:
                        event = await subscriber.get_message(timeout=1)
                        if event and event['type'] == 'subscribe':
                            self.ready = True
                            self.started.set()
                        elif event and event['type'] == 'message':
                            try:
                                data = json.loads(event['data'])
                                await user_connections.broadcast(int(data['user_id']), data['event'])
                            except (ValueError, KeyError, TypeError):
                                logger.warning('Invalid user event ignored')
            except (RedisError, OSError):
                self.ready = False
                await user_connections.close_all()
                await asyncio.sleep(1)

    async def send(self, user_id, event):
        if self.redis:
            async with asyncio.timeout(3):
                await self.redis.publish('connect:users', json.dumps({'user_id': user_id, 'event': event}))
        else:
            await user_connections.broadcast(user_id, event)


user_events = UserEvents()
