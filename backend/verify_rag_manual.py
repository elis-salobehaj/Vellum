import sys
import os
import asyncio
from dotenv import load_dotenv

# Ensure we can import app
sys.path.append(os.path.join(os.getcwd(), 'backend'))
load_dotenv()

# Mock Settings if needed, but we used env vars
os.environ["CHROMA_HOST"] = "localhost"
os.environ["CHROMA_PORT"] = "8001"

try:
    from app.services.rag_service import rag_service
    from app.models.schemas import Citation
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

async def test_retrieval():
    print("🚀 Testing RAG Service Retrieval...")
    query = "What is agentic AI?"
    print(f"❓ Query: {query}")
    
    try:
        citations = await rag_service.query(query, k=3)
        print(f"✅ Retrieved {len(citations)} citations.")
        for i, c in enumerate(citations):
            print(f"   [{i+1}] {c.source} (Score: {round(c.score, 4)})")
            print(f"       Length: {len(c.text)} characters")
            print(f"       Snippet: {c.text[:300]}...") # Show more to prove it's > 200
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
