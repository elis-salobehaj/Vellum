from app.core.config import settings

print(f"DEBUG: OPENAI_API_KEY is {'SET' if settings.OPENAI_API_KEY else 'NOT SET'}")
print(f"DEBUG: EMBEDDING_MODEL_NAME is {settings.EMBEDDING_MODEL_NAME}")
