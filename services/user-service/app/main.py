from fastapi import FastAPI


app = FastAPI(
    title="Connect User Service",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "service": "user-service",
        "status": "ok",
    }