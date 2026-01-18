from fastapi import APIRouter
from app.api.endpoints import chat, admin, history

api_router = APIRouter()
api_router.include_router(chat.router, tags=["chat"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
