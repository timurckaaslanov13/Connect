from fastapi import FastAPI
from sqlalchemy import text
from app.database.connection import engine
from app.api.auth import router as auth_router



app = FastAPI(
    title="Connect Auth Service",
    version="0.1.0",
)

app.include_router(auth_router)

@app.get("/health")
def health():
    return{
        "service": "auth-service",
        "status": "ok",
    }
    
@app.get("/version")
def version():
    return{
        "version": "0.1.0"
    }

@app.get("/health/database")
def database_health():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))

    return {
        "database": "postgresql",
        "status": "ok",
    }