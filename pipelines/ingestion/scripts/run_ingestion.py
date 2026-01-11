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
    prefix: str,
    chunk_size: int = 1024,
    chunk_overlap: int = 20,
    splitter_mode: str = "fixed",
    breakpoint_threshold: int = 95,
    max_docs: int = 5
):
    print(f"🚀 Starting ingestion logic (Max Docs: {max_docs})...")
    
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
    
    # Sort to ensure deterministic selection for experiments
    files.sort()
    
    if max_docs > 0 and len(files) > max_docs:
        print(f"📉 Limiting ingestion to first {max_docs} files (found {len(files)}).")
        files = files[:max_docs]
    
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

    # 5. Chunking Configuration
    if splitter_mode == "semantic":
        print(f"✂️ Configuring Semantic Splitter (Threshold: {breakpoint_threshold})...")
        text_splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=breakpoint_threshold,
            embed_model=Settings.embed_model
        )
    else:
        print(f"✂️ Configuring Fixed Splitter (Size: {chunk_size}, Overlap: {chunk_overlap})...")
        # Ensure imports
        from llama_index.core.node_parser import SentenceSplitter
        text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
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

    # 7. Evaluation (Simple Hit Rate Proxy)
    # We query for a generic term that likely appears in AI papers and check provided count.
    # In a real setup, we'd use a Golden Dataset.
    print("⚖️ Running Evaluation...")
    # Re-connect (read-only)
    eval_vector_store = ChromaVectorStore(chroma_collection=collection)
    eval_index = VectorStoreIndex.from_vector_store(
        eval_vector_store,
        embed_model=Settings.embed_model
    )
    retriever = eval_index.as_retriever(similarity_top_k=3)
    
    # Test Query
    query = "agentic ai"
    results = retriever.retrieve(query)
    
    # Validation Metric: Did we get results?
    # For Katib to optimize, we want a float. 
    # Let's use 'average score' of top 3 docs as a proxy for relevance for now.
    avg_score = 0.0
    if results:
        for r in results:
            print(f"   found: {r.node.metadata.get('file_name')} (Score: {r.score})")
            avg_score += (r.score if r.score else 0.0)
        avg_score = avg_score / len(results)
    
    print(f"accuracy={avg_score:.4f}")

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

    # Tuning Args
    parser.add_argument("--chunk_size", type=int, default=1024)
    parser.add_argument("--chunk_overlap", type=int, default=20)
    parser.add_argument("--splitter_mode", type=str, default="fixed", choices=["fixed", "semantic"])
    parser.add_argument("--breakpoint_threshold", type=int, default=95)
    parser.add_argument("--max_docs", type=int, default=5)

    args = parser.parse_args()
    ingest(
        args.chroma_host, 
        args.chroma_port,
        args.minio_endpoint,
        args.minio_access_key,
        args.minio_secret_key,
        args.bucket,
        args.prefix,
        args.chunk_size,
        args.chunk_overlap,
        args.splitter_mode,
        args.breakpoint_threshold,
        args.max_docs
    )
