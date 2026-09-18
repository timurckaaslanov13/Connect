from fastapi import FastAPI
from app.api.chats import router as chats_router

app = FastAPI(
    title="Connect Chat Service",
    version="0.1.0",
)
app.include_router(chats_router)


@app.get("/health")
def health():
    return {
        "service": "chat-service",
        "status": "ok",
    }