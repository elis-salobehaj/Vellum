import os
import argparse
import chromadb
from minio import Minio
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings
from llama_index.core.node_parser import SemanticSplitterNodeParser

def download_from_minio(minio_client, bucket: str, prefix: str, local_dir: str):
    print(f"📥 Downloading from MinIO {bucket}/{prefix} to {local_dir}...")
    objects = minio_client.list_objects(bucket, prefix=prefix, recursive=True)
    count = 0
    for obj in objects:
        if obj.is_dir:
            continue
        file_path = os.path.join(local_dir, obj.object_name)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        minio_client.fget_object(bucket, obj.object_name, file_path)
        count += 1
    print(f"✅ Downloaded {count} files.")

def ingest(
    chroma_host: str, 
    chroma_port: int,
    minio_endpoint: str,
    minio_access_key: str,
    minio_secret_key: str,
    bucket: str,
    prefix: str
):
    print(f"🚀 Starting ingestion logic...")
    
    # 0. Setup Local Data Directory
    input_dir = "/app/data/downloads"
    os.makedirs(input_dir, exist_ok=True)

    # 1. Connect to MinIO and Download
    # Note: KFP MinIO service is usually at 'minio-service.kubeflow.svc:9000'
    secure = False # Internal K8s service is usually HTTP
    minio_client = Minio(
        minio_endpoint,
        access_key=minio_access_key,
        secret_key=minio_secret_key,
        secure=secure
    )
    
    download_from_minio(minio_client, bucket, prefix, input_dir)

    # 2. Connect to ChromaDB (Remote)
    print(f"🔌 Connecting to ChromaDB at {chroma_host}:{chroma_port}")
    chroma_client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
    collection = chroma_client.get_or_create_collection("kbase_docs")
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # 3. Configure Embeddings
    print("⚙️ Loading Embedding Model (BAAI/bge-large-en-v1.5)...")
    Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")

    # 4. Load Documents
    print("📂 Reading documents...")
    # LlamaIndex SimpleDirectoryReader doesn't expose a per-file callback easily in load_data(),
    # but we can list files first to show what we found.
    files = []
    for root, _, filenames in os.walk(input_dir):
        for filename in filenames:
            if filename.lower().endswith(('.pdf', '.txt', '.md', '.docx')):
                files.append(os.path.join(root, filename))
    
    print(f"Found {len(files)} files to process:")
    for f in files[:10]: # Print first 10
        print(f" - {os.path.basename(f)}")
    if len(files) > 10:
        print(f" ...and {len(files)-10} more.")

    reader = SimpleDirectoryReader(
        input_dir=input_dir,
        recursive=True,
        required_exts=[".pdf", ".txt", ".md", ".docx"]
    )
    documents = reader.load_data()
    print(f"📄 Loaded {len(documents)} document objects.")

    if not documents:
        print("⚠️ No documents found. Exiting.")
        return

    # 5. Semantic Chunking
    print("✂️ Configuring Semantic Splitter...")
    text_splitter = SemanticSplitterNodeParser(
        buffer_size=1,
        breakpoint_percentile_threshold=95,
        embed_model=Settings.embed_model
    )

    # 6. Indexing
    print("🧠 Indexing documents...")
    index = VectorStoreIndex.from_documents(
        documents,
        storage_context=storage_context,
        transformations=[text_splitter],
        show_progress=True
    )
    print("✅ Ingestion Complete!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents from MinIO to ChromaDB")
    # MinIO Args
    parser.add_argument("--minio_endpoint", type=str, default="minio-service.kubeflow.svc:9000")
    parser.add_argument("--minio_access_key", type=str, default="minio")
    parser.add_argument("--minio_secret_key", type=str, default="minio123")
    parser.add_argument("--bucket", type=str, required=True)
    parser.add_argument("--prefix", type=str, default="")
    
    # Chroma Args
    parser.add_argument("--chroma_host", type=str, default="chroma-service.kubeflow.svc.cluster.local")
    parser.add_argument("--chroma_port", type=int, default=8000)

    args = parser.parse_args()
    ingest(
        args.chroma_host, 
        args.chroma_port,
        args.minio_endpoint,
        args.minio_access_key,
        args.minio_secret_key,
        args.bucket,
        args.prefix
    )
