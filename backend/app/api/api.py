from fastapi import APIRouter
from app.api.endpoints import chat, admin, history, health, files

api_router = APIRouter()
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(health.router, tags=["health"])
api_router.include_router(files.router, prefix="/files", tags=["files"])
