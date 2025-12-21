from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.core.auth import get_current_user
from app.services.history_service import history_service
from pydantic import BaseModel

router = APIRouter()

class ConversationSummary(BaseModel):
    id: str
    title: str
    date: str

@router.get("/", response_model=List[ConversationSummary])
async def get_history(current_user: dict = Depends(get_current_user)):
    # In a real app, we'd filter by current_user['id']
    return history_service.get_recent_conversations(user_id="default")

@router.get("/{session_id}")
async def get_conversation(session_id: str, current_user: dict = Depends(get_current_user)):
    messages = history_service.get_messages(session_id)
    if not messages:
         # If new session, return empty
         return []
    return messages
