from typing import List, Dict
import datetime
from app.core.logging import logger

# In-memory storage for MVP. Replace with SQLite or Postgres.
# Structure: { session_id: { "title": "...", "updated_at": datetime, "messages": [...] } }
CONVERSATIONS = {}

class HistoryService:
    def get_recent_conversations(self, user_id: str, limit: int = 10):
        # Filter by user_id if we had multi-user structure
        # Sort by updated_at desc
        logger.debug("history_get_recent", user_id=user_id, limit=limit)
        convs = []
        for cid, data in CONVERSATIONS.items():
            convs.append({
                "id": cid,
                "title": data["title"],
                "date": data["updated_at"].strftime("%b %d")
            })
        return sorted(convs, key=lambda x: x['date'], reverse=True)[:limit]

    def add_message(self, session_id: str, role: str, content: str, citations: List[Dict] = None):
        if session_id not in CONVERSATIONS:
            logger.info("history_session_created", session_id=session_id)
            CONVERSATIONS[session_id] = {
                "title": content[:30] + "...",
                "updated_at": datetime.datetime.now(),
                "messages": []
            }
        
        logger.debug("history_add_message", session_id=session_id, role=role)
        message_data = {"role": role, "content": content}
        if citations:
            message_data["citations"] = citations
            
        CONVERSATIONS[session_id]["messages"].append(message_data)
        CONVERSATIONS[session_id]["updated_at"] = datetime.datetime.now()

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        messages = CONVERSATIONS.get(session_id, {}).get("messages", [])
        logger.debug("history_get_messages", session_id=session_id, count=len(messages))
        return messages

history_service = HistoryService()
