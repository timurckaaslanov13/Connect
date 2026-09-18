from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from app.api.messages import router as messages_router
from app.api.websocket import router as websocket_router
from app.websocket.events import events


@asynccontextmanager
async def lifespan(app: FastAPI):
    await events.start()
    try:
        yield
    finally:
        await events.stop()


app = FastAPI(title='Connect Message Service', version='0.1.0', lifespan=lifespan)
app.include_router(messages_router)
app.include_router(websocket_router)


@app.get('/health')
def health():
    if events.redis_url and not events.ready:
        raise HTTPException(status_code=503, detail='Message subscription unavailable')
    return {'service': 'message-service', 'status': 'ok'}
