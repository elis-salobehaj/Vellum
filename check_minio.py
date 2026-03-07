from minio import Minio

client = Minio(
    "localhost:9000", access_key="minio", secret_key="minio123", secure=False
)
buckets = client.list_buckets()
for b in buckets:
    print(f"Bucket: {b.name}")
    objects = client.list_objects(b.name)
    for obj in objects:
        print(f" - {obj.object_name}")
