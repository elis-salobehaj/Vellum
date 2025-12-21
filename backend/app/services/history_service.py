from typing import List, Dict
import datetime

# In-memory storage for MVP. Replace with SQLite or Postgres.
# Structure: { session_id: { "title": "...", "updated_at": datetime, "messages": [...] } }
CONVERSATIONS = {}

class HistoryService:
    def get_recent_conversations(self, user_id: str, limit: int = 10):
        # Filter by user_id if we had multi-user structure
        # Sort by updated_at desc
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
            CONVERSATIONS[session_id] = {
                "title": content[:30] + "...",
                "updated_at": datetime.datetime.now(),
                "messages": []
            }
        
        message_data = {"role": role, "content": content}
        if citations:
            message_data["citations"] = citations
            
        CONVERSATIONS[session_id]["messages"].append(message_data)
        CONVERSATIONS[session_id]["updated_at"] = datetime.datetime.now()

    def get_messages(self, session_id: str) -> List[Dict[str, str]]:
        return CONVERSATIONS.get(session_id, {}).get("messages", [])

history_service = HistoryService()
