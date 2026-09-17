from fastapi import FastAPI
app = FastAPI(
    title="Connect Auth Service",
    version="0.1.0",
)

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