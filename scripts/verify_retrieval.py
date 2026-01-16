import sys
import os

# Ensure backend modules are importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

# Mock Settings if needed, or rely on .env
# We need to set env vars for qdrant
os.environ["QDRANT_HOST"] = "localhost" # Using port-forward
os.environ["QDRANT_PORT"] = "6333"

from app.services.rag_service import rag_service
import asyncio

async def test_retrieval():
    print("🔎 Testing Retrieval (Agentic AI)...")
    try:
        results = await rag_service.query("Agentic AI", k=3)
        if results:
            print(f"✅ Retrieved {len(results)} chunks:")
            for r in results:
                print(f"   - {r.source} (Score: {r.score:.4f})")
                print(f"     Preview: {r.text[:100]}...")
        else:
            print("⚠️ No results found.")
    except Exception as e:
        print(f"❌ Retrieval failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_retrieval())
