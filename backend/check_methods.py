import qdrant_client
import asyncio


async def check():
    client = qdrant_client.AsyncQdrantClient(host="localhost", port=6333)
    print(f"AsyncQdrantClient has 'search': {hasattr(client, 'search')}")
    print(f"AsyncQdrantClient has 'query_points': {hasattr(client, 'query_points')}")
    print(f"Methods: {[m for m in dir(client) if not m.startswith('_')]}")


asyncio.run(check())
