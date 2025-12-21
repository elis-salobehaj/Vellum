import asyncio
import os
import sys

# Add parent dir to path so we can import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.rag_service import rag_service
from dotenv import load_dotenv

load_dotenv()

async def main():
    source_dir = "data/source_documents"
    print(f"Ingesting documents from {source_dir}...")
    
    result = await rag_service.ingest_documents(source_dir)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
