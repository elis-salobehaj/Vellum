import os
import argparse
from minio import Minio
from minio.error import S3Error

def upload_docs(local_dir, bucket_name, endpoint, access_key, secret_key, clean_bucket=False):
    print(f"🔌 Connecting to MinIO at {endpoint}...")
    # For localhost upload, we usually use secure=False
    client = Minio(
        endpoint,
        access_key=access_key,
        secret_key=secret_key,
        secure=False
    )

    # Make bucket if not exists
    if not client.bucket_exists(bucket_name):
        print(f"📦 Creating bucket '{bucket_name}'...")
        client.make_bucket(bucket_name)
    else:
        print(f"📦 Bucket '{bucket_name}' exists.")
        if clean_bucket:
            print(f"🧹 Cleaning bucket '{bucket_name}'...")
            objects = client.list_objects(bucket_name, recursive=True)
            for obj in objects:
                client.remove_object(bucket_name, obj.object_name)
            print(f"✨ Bucket cleaned.")

    print(f"📂 Uploading files from {local_dir}...")
    count = 0
    if not os.path.exists(local_dir):
         print(f"⚠️ Local directory {local_dir} does not exist!")
         return

    for root, dirs, files in os.walk(local_dir):
        for file in files:
            file_path = os.path.join(root, file)
            # Create object name (preserve relative path)
            rel_path = os.path.relpath(file_path, local_dir)
            object_name = rel_path.replace("\\", "/") # Ensure forward slashes
            
            print(f"   ⬆️ Uploading {object_name}...")
            client.fput_object(bucket_name, object_name, file_path)
            count += 1
            
    print(f"✅ Successfully uploaded {count} files to '{bucket_name}'.")

if __name__ == "__main__":
    # Defaults assume forwarded port 9000 -> localhost:9000
    parser = argparse.ArgumentParser()
    parser.add_argument("--local_dir", default="backend/data/source_documents")
    parser.add_argument("--bucket", default="documents")
    parser.add_argument("--endpoint", default="localhost:9000") 
    parser.add_argument("--access_key", default="minio")
    parser.add_argument("--secret_key", default="minio123")
    parser.add_argument("--clean_bucket", action="store_true", help="Delete all existing files in the bucket before uploading")
    
    args = parser.parse_args()
    upload_docs(args.local_dir, args.bucket, args.endpoint, args.access_key, args.secret_key, args.clean_bucket)
