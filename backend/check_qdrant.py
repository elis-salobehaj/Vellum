import qdrant_client
from app.core.config import settings

client = qdrant_client.QdrantClient(
    host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
)
collection_name = settings.QDRANT_COLLECTION

info = client.get_collection(collection_name)
print(f"Collection {collection_name} has {info.points_count} points.")
