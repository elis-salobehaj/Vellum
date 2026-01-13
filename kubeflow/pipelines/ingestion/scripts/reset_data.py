from minio import Minio
import os

# Configuration
MINIO_ENDPOINT = "localhost:9000"
ACCESS_KEY = "minio"
SECRET_KEY = "minio123"
BUCKET = "documents"

SOURCE_DIR = "/mnt/d/projects/Vellum/backend/data/source_documents"
FILES_TO_UPLOAD = [
    "OpenAI a-practical-guide-to-building-agents.pdf",
    "Architectures for Building Agentic AI.pdf"
]

def reset_and_upload():
    print(f"🔌 Connecting to MinIO at {MINIO_ENDPOINT}...")
    try:
        client = Minio(
            MINIO_ENDPOINT,
            access_key=ACCESS_KEY,
            secret_key=SECRET_KEY,
            secure=False
        )

        # 1. Clean Bucket
        if client.bucket_exists(BUCKET):
            print(f"🗑️  Cleaning bucket '{BUCKET}'...")
            objects = client.list_objects(BUCKET, recursive=True)
            for obj in objects:
                client.remove_object(BUCKET, obj.object_name)
                print(f"   - Deleted {obj.object_name}")
        else:
            client.make_bucket(BUCKET)
            print(f"🆕 Created bucket '{BUCKET}'")

        # 2. Upload Files
        print(f"📂 Uploading {len(FILES_TO_UPLOAD)} documents...")
        for filename in FILES_TO_UPLOAD:
            file_path = os.path.join(SOURCE_DIR, filename)
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                continue
            
            # Put object
            client.fput_object(BUCKET, filename, file_path)
            print(f"   - Uploaded {filename}")

        print("✅ Data reset complete.")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    reset_and_upload()
