from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine
from app.api.friends import router as friends_router
from app.api.users import router as users_router

app = FastAPI(
    title="Connect User Service",
    version="0.1.0",
)

app.include_router(users_router)
app.include_router(friends_router)

@app.get("/health")
def health():
    return {
        "service": "user-service",
        "status": "ok",
    }


@app.get("/health/database")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "database": "postgresql",
        "status": "ok",
    }