from fastapi import FastAPI
from app.api.messages import router as messages_router

app = FastAPI(
    title="Connect Message Service",
    version="0.1.0",
)
app.include_router(messages_router)

@app.get("/health")
def health():
    return {
        "service": "message-service",
        "status": "ok",
    }