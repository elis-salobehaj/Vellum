import os
from minio import Minio

# Configuration
MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "minio"
SECRET_KEY = "minio123"
BUCKET = "documents"

def list_documents():
    print(f"🔌 Connecting to MinIO at {MINIO_ENDPOINT}...")
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            secure=False
        )

        if not client.bucket_exists(BUCKET):
            print(f"❌ Bucket '{BUCKET}' does not exist.")
            return

        print(f"📂 Listing objects in bucket '{BUCKET}':")
        objects = client.list_objects(BUCKET, recursive=True)
        
        count = 0
        for obj in objects:
            print(f" - {obj.object_name} ({obj.size} bytes)")
            count += 1
            
        print(f"\n✅ Total Documents: {count}")

    except Exception as e:
        print(f"❌ Error connecting to MinIO: {e}")
        print("💡 Hint: Make sure you have port-forwarded MinIO: './scripts/connect.sh'")

if __name__ == "__main__":
    list_documents()
