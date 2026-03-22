import qdrant_client
from qdrant_client.http import models
from app.core.config import settings

client = qdrant_client.QdrantClient(
    host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
)

collection_name = settings.QDRANT_COLLECTION

print(f"Checking collection: {collection_name}")
try:
    info = client.get_collection(collection_name)
    print(f"Current dim: {info.config.params.vectors.size}")
    print(f"Deleting collection {collection_name}...")
    client.delete_collection(collection_name)
    print("Deleted.")
except Exception as e:
    print(f"Error or collection not found: {e}")

print(f"Creating collection {collection_name} with dim 1536...")

client.create_collection(
    collection_name=collection_name,
    vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
)
print("Created successfully.")
