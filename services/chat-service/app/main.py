from fastapi import FastAPI


app = FastAPI(
    title="Connect Chat Service",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "chat-service",
        "status": "ok",
    }