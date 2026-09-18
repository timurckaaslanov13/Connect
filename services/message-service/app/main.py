from fastapi import FastAPI


app = FastAPI(
    title="Connect Message Service",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "message-service",
        "status": "ok",
    }