from fastapi import FastAPI
from src.backend.app.api.router import api_router
from src.backend.app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

app.include_router(api_router)

@app.get("/")
def root():
    return {
        "message": f"{settings.app_name} is running"
    }