"""Best-effort live fan-out. PostgreSQL history remains the source of truth."""
import asyncio
from contextlib import suppress
import json
import logging

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.config import settings
from app.schemas.message import MessageResponse
from app.websocket.manager import manager

logger = logging.getLogger(__name__)
CHANNEL = 'connect:messages'


class MessageEvents:
    def __init__(self, redis_url: str | None):
        self.redis_url = redis_url
        self.redis = None
        self.task = None
        self.ready = False
        self.started = None

    async def start(self):
        if not self.redis_url:
            self.ready = True
            return
        self.redis = Redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=3)
        self.started = asyncio.Event()
        self.task = asyncio.create_task(self._listen())
        try:
            await asyncio.wait_for(self.started.wait(), 15)
        except BaseException:
            await self.stop()
            raise

    async def stop(self):
        if self.task:
            self.task.cancel()
            with suppress(asyncio.CancelledError):
                await self.task
            self.task = None
        if self.redis:
            await self.redis.aclose()
            self.redis = None
        self.ready = False
        await manager.close_all()

    async def _listen(self):
        while True:
            try:
                async with self.redis.pubsub() as pubsub:
                    await pubsub.subscribe(CHANNEL)
                    # Wait for the subscription acknowledgement before accepting traffic.
                    async with asyncio.timeout(5):
                        while True:
                            event = await pubsub.get_message(ignore_subscribe_messages=False, timeout=1)
                            if event and event['type'] == 'subscribe':
                                break
                    self.ready = True
                    self.started.set()
                    while True:
                        event = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1)
                        if event is not None and event['type'] == 'message':
                            try:
                                message = MessageResponse.model_validate_json(event['data'])
                            except ValueError:
                                logger.warning('Ignoring invalid message event')
                                continue
                            await manager.broadcast(message.chat_id, message.model_dump(mode='json'))
            except (RedisError, OSError, TimeoutError):
                self.ready = False
                logger.warning('Message subscription unavailable; clients must reload history')
                await manager.close_all()
                await asyncio.sleep(1)

    async def publish(self, chat_id: int, data: dict):
        if not self.redis_url:
            await manager.broadcast(chat_id, data)
            return
        try:
            if self.redis is None or not self.ready:
                raise ConnectionError('Message subscriber is not ready')
            async with asyncio.timeout(3):
                await self.redis.publish(CHANNEL, json.dumps(data))
        except (RedisError, OSError, TimeoutError):
            # The database transaction already committed. Do not turn a successful
            # save into an HTTP error that encourages a duplicate retry.
            logger.warning('Message saved but live notification failed; reload history')
            await manager.close_all()


events = MessageEvents(settings.redis_url)
