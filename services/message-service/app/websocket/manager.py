from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, list[WebSocket]] = {}

    async def connect(
        self,
        chat_id: int,
        websocket: WebSocket,
    ) -> None:
        await websocket.accept()

        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = []

        self.active_connections[chat_id].append(websocket)

    def disconnect(
        self,
        chat_id: int,
        websocket: WebSocket,
    ) -> None:
        connections = self.active_connections.get(chat_id)

        if connections is None:
            return

        if websocket in connections:
            connections.remove(websocket)

        if not connections:
            del self.active_connections[chat_id]

    async def broadcast(
        self,
        chat_id: int,
        data: dict,
    ) -> None:
        connections = self.active_connections.get(
            chat_id,
            [],
        )

        for connection in connections.copy():
            try:
                await connection.send_json(data)

            except Exception:
                self.disconnect(
                    chat_id,
                    connection,
                )


manager = ConnectionManager()