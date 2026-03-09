import os
import argparse
import qdrant_client
from llama_index.core import Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.core.ingestion import IngestionPipeline


def ingest(
    qdrant_host: str,
    qdrant_port: int,
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    bucket: str,
    prefix: str,
    chunk_size: int = 1024,
    chunk_overlap: int = 20,
    splitter_mode: str = "fixed",
    breakpoint_threshold: int = 95,
    max_docs: int = 15,
    top_k: int = 3,
    model_name: str = "BAAI/bge-small-en-v1.5",
    embeddings_service_url: str = "http://embeddings-service.kubeflow-vellum/v1",
    openai_api_key: str = "EMPTY",
    cleanup: bool = False,
):
    print(f"🚀 Starting STREAMING ingestion logic (Max Docs: {max_docs})...")

    # 1. Connect to Qdrant
    print(f"🔌 Connecting to Qdrant at {qdrant_host}:{qdrant_port}")
    client = qdrant_client.QdrantClient(host=qdrant_host, port=qdrant_port)
    collection_name = "vellum"

    if cleanup:
        print(f"🧹 Cleaning up collection '{collection_name}'...")
        if client.collection_exists(collection_name):
            client.delete_collection(collection_name)

        # We need to recreate it with correct parameters
        from qdrant_client.http.models import VectorParams, Distance

        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    vector_store = QdrantVectorStore(client=client, collection_name=collection_name)

    # 2. Configure Embeddings (OpenAI API)
    print(f"⚙️ Connecting to Embedding Service ({model_name})...")
    Settings.embed_model = OpenAIEmbedding(
        model_name=model_name,
        api_base=embeddings_service_url,
        api_key=openai_api_key,
        embed_batch_size=30,
    )

    # 3. Configure Splitter
    if splitter_mode == "semantic":
        print(f"✂️ Configuring Semantic Splitter (Threshold: {breakpoint_threshold})...")
        text_splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=breakpoint_threshold,
            embed_model=Settings.embed_model,
        )
    else:
        print(
            f"✂️ Configuring Fixed Splitter (Size: {chunk_size}, Overlap: {chunk_overlap})..."
        )
        text_splitter = SentenceSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    # 4. Setup Ingestion Pipeline (Pro Solution)
    # This allows us to process documents one by one and push to vector store
    pipeline = IngestionPipeline(
        transformations=[text_splitter, Settings.embed_model],
        vector_store=vector_store,
    )

    # 5. Connect to MinIO via S3Reader
    # Ensure endpoint has http:// prefix for S3Reader if not present
    s3_url = minio_endpoint
    if not s3_url.startswith("http"):
        s3_url = f"http://{s3_url}"

    print(f"📡 Connecting to MinIO: {s3_url}/{bucket}")

    # 6. Iterative Processing (Download & Local Load)
    print(f"📂 Downloading documents from MinIO bucket '{bucket}'...")
    from minio import Minio

    m_client = Minio(
        minio_endpoint.replace("http://", "").replace("https://", ""),
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=False,
    )

    import shutil

    temp_dir = "/tmp/vellum-ingest"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)

    objects = m_client.list_objects(bucket, prefix=prefix, recursive=True)
    files = [obj.object_name for obj in objects if not obj.is_dir]
    files.sort()

    if max_docs > 0 and len(files) > max_docs:
        files = files[:max_docs]

    print(f"✅ Found {len(files)} files to download.")

    for file_key in files:
        target_path = os.path.join(temp_dir, os.path.basename(file_key))
        print(f"   📥 Downloading {file_key} -> {target_path}")
        m_client.fget_object(bucket, file_key, target_path)

    print("📂 Loading documents from temp directory...")
    from llama_index.core import SimpleDirectoryReader

    reader = SimpleDirectoryReader(input_dir=temp_dir)
    documents = reader.load_data()

    print(f"🔄 Running ingestion pipeline on {len(documents)} document chunks...")
    pipeline.run(documents=documents)

    print("✅ Ingestion Complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Ingest documents from MinIO to Qdrant via Streaming"
    )
    parser.add_argument(
        "--minio_endpoint", type=str, default="minio-service.kubeflow.svc:9000"
    )
    parser.add_argument("--minio_access_key", type=str, default="minio")
    parser.add_argument("--minio_secret_key", type=str, default="minio123")
    parser.add_argument("--bucket", type=str, required=True)
    parser.add_argument("--prefix", type=str, default="")
    parser.add_argument(
        "--qdrant_host", type=str, default="qdrant.qdrant.svc.cluster.local"
    )
    parser.add_argument("--qdrant_port", type=int, default=6333)
    parser.add_argument("--chunk_size", type=int, default=512)
    parser.add_argument("--chunk_overlap", type=int, default=20)
    parser.add_argument(
        "--splitter_mode", type=str, default="fixed", choices=["fixed", "semantic"]
    )
    parser.add_argument("--breakpoint_threshold", type=int, default=95)
    parser.add_argument("--max_docs", type=int, default=15)
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--model_name", type=str, default="BAAI/bge-small-en-v1.5")
    parser.add_argument(
        "--embeddings_service_url",
        type=str,
        default="http://embeddings-service.kubeflow-vellum/v1",
    )
    parser.add_argument("--openai_api_key", type=str, default="EMPTY")
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Delete and recreate collection before ingestion",
    )

    args = parser.parse_args()
    ingest(
        args.qdrant_host,
        args.qdrant_port,
        args.minio_endpoint,
        args.minio_access_key,
        args.minio_secret_key,
        args.bucket,
        args.prefix,
        args.chunk_size,
        args.chunk_overlap,
        args.splitter_mode,
        args.breakpoint_threshold,
        args.max_docs,
        args.top_k,
        args.model_name,
        args.embeddings_service_url,
        args.openai_api_key,
        args.cleanup,
    )
