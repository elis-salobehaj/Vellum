from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.auth import get_current_user
from app.services.history_service import history_service
from app.core.logging import logger
from pydantic import BaseModel

router = APIRouter()

class ConversationSummary(BaseModel):
    id: str
    title: str
    date: str

@router.get("", response_model=List[ConversationSummary])
async def get_history(current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user", "default")
    logger.info("history_fetch_list", user=user_id)
    return history_service.get_recent_conversations(user_id=user_id)

@router.get("/{session_id}")
async def get_conversation(session_id: str, current_user: dict = Depends(get_current_user)):
    user_id = current_user.get("user", "default")
    logger.info("history_fetch_session", user=user_id, session_id=session_id)
    messages = history_service.get_messages(session_id)
    if not messages:
         logger.debug("history_session_empty", session_id=session_id)
         return []
    return messages
