import asyncio

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}
        self._send_locks: dict[WebSocket, asyncio.Lock] = {}

    async def connect(self, chat_id: int, websocket: WebSocket, *, accepted: bool = False) -> None:
        if not accepted:
            await websocket.accept()
        self.active_connections.setdefault(chat_id, []).append(websocket)
        self._send_locks[websocket] = asyncio.Lock()

    def disconnect(self, chat_id: int, websocket: WebSocket) -> None:
        connections = self.active_connections.get(chat_id)
        if connections and websocket in connections:
            connections.remove(websocket)
            if not connections:
                del self.active_connections[chat_id]
        self._send_locks.pop(websocket, None)

    async def _send(self, chat_id: int, connection: WebSocket, data: dict):
        lock = self._send_locks.get(connection)
        if lock is None:
            return
        try:
            async with asyncio.timeout(3):
                async with lock:
                    await connection.send_json(data)
        except Exception:
            self.disconnect(chat_id, connection)
            try:
                async with asyncio.timeout(1):
                    await connection.close(code=1013)
            except Exception:
                pass

    async def broadcast(self, chat_id: int, data: dict) -> None:
        connections = self.active_connections.get(chat_id, []).copy()
        await asyncio.gather(*(self._send(chat_id, connection, data) for connection in connections))

    async def close_all(self, code: int = 1012):
        connections = [(chat, ws) for chat, items in self.active_connections.items() for ws in items.copy()]
        for chat, ws in connections:
            self.disconnect(chat, ws)
        async def close(ws):
            try:
                async with asyncio.timeout(1):
                    await ws.close(code=code)
            except Exception:
                pass
        await asyncio.gather(*(close(ws) for _, ws in connections))


manager = ConnectionManager()
