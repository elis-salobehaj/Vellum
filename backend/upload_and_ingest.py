import os
import sys
import httpx
from minio import Minio


def main():
    minio_endpoint = "localhost:9000"
    access_key = "minio"
    secret_key = "minio123"
    bucket_name = "documents"
    source_dir = os.path.join(os.path.dirname(__file__), "data", "source_documents")
    backend_url = "http://localhost:8006/api/v1/admin/upload-and-ingest"
    headers = {"kubeflow-userid": "vellum@example.com"}

    print("🚀 Starting Upload & Ingest Process...")

    # 1. Initialize Minio Client
    try:
        client = Minio(
            minio_endpoint, access_key=access_key, secret_key=secret_key, secure=False
        )
        print("✅ Connected to Minio.")
    except Exception as e:
        print(f"❌ Failed to connect to Minio: {e}")
        sys.exit(1)

    # 2. Create Bucket if not exists
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            print(f"✅ Created bucket '{bucket_name}'.")
        else:
            print(f"ℹ️  Bucket '{bucket_name}' already exists.")
    except Exception as e:
        print(f"❌ Failed to ensure bucket exists: {e}")
        sys.exit(1)

    # 3. Upload Files
    files = [
        f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))
    ]
    if not files:
        print("⚠️  No files found in source directory.")

    for filename in files:
        file_path = os.path.join(source_dir, filename)
        try:
            client.fput_object(bucket_name, filename, file_path)
            print(f"   ⬆️  Uploaded: {filename}")
        except Exception as e:
            print(f"   ❌ Failed to upload {filename}: {e}")

    # 4. Trigger direct ingestion through the current admin endpoint.
    print("🔄 Triggering admin upload-and-ingest flow...")
    try:
        response = httpx.post(
            backend_url,
            params={"cleanup": "true", "reset_progress": "true"},
            headers=headers,
            timeout=60.0,
        )
        if response.status_code == 200:
            print("✅ Ingestion triggered successfully.")
            print(response.text[:2000])
        else:
            print(f"❌ Ingestion Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Failed to call Backend API: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
