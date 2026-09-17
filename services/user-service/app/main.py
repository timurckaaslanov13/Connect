from fastapi import FastAPI
from sqlalchemy import text

from app.database.connection import engine


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


@app.get("/health/database")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "database": "postgresql",
        "status": "ok",
    }