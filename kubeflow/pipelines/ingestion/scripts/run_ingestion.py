import os
import argparse
import qdrant_client
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.readers.s3 import S3Reader
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
    cleanup: bool = False
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
    
    # 2. Configure Embeddings (Remote TEI Service)
    print(f"⚙️ Connecting to Remote Embedding Service ({model_name})...")
    from llama_index.embeddings.openai import OpenAIEmbedding
    Settings.embed_model = OpenAIEmbedding(
        model_name=model_name,
        api_base=os.getenv("EMBEDDINGS_SERVICE_URL", "http://embeddings-service.kubeflow-user-example-com/v1"),
        api_key="EMPTY",
        embed_batch_size=30
    )

    # 3. Configure Splitter
    if splitter_mode == "semantic":
        print(f"✂️ Configuring Semantic Splitter (Threshold: {breakpoint_threshold})...")
        text_splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=breakpoint_threshold,
            embed_model=Settings.embed_model
        )
    else:
        print(f"✂️ Configuring Fixed Splitter (Size: {chunk_size}, Overlap: {chunk_overlap})...")
        text_splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
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

    print(f"📡 Connecting to MinIO via S3Reader: {s3_url}/{bucket}")
    loader = S3Reader(
        bucket=bucket,
        aws_access_id=minio_access_key,
        aws_access_secret=minio_secret_key,
        s3_endpoint_url=s3_url
    )

    # 6. Iterative Processing (Streaming)
    print("📂 Listing documents in MinIO...")
    files = loader.list_resources(prefix=prefix)
    files.sort()
    
    if max_docs > 0 and len(files) > max_docs:
        print(f"📉 Limiting ingestion to first {max_docs} files (found {len(files)}).")
        files = files[:max_docs]

    print(f"✅ Found {len(files)} files to process.")
    
    processed_count = 0
    for file_key in files:
        print(f"🔄 Processing [{processed_count+1}/{len(files)}]: {file_key}...")
        try:
            # Load documents (returns a list)
            documents = loader.load_resource(file_key)
            
            # Run pipeline for these documents
            pipeline.run(documents=documents)
            
            processed_count += 1
            # In a real pro setup, we might clear doc from memory here
            # del documents 
        except Exception as e:
            print(f"⚠️ Error processing {file_key}: {e}")

    print(f"✅ Ingestion Complete! Processed {processed_count} files.")

    # 7. Evaluation (Simple Hit Rate Proxy)
    print("⚖️ Running Evaluation...")
    eval_index = VectorStoreIndex.from_vector_store(
        vector_store,
        embed_model=Settings.embed_model
    )
    retriever = eval_index.as_retriever(similarity_top_k=top_k)
    
    query = "agentic ai"
    results = retriever.retrieve(query)
    
    avg_score = 0.0
    if results:
        for r in results:
            print(f"   found: {r.node.metadata.get('file_name')} (Score: {r.score})")
            avg_score += (r.score if r.score else 0.0)
        avg_score = avg_score / len(results)
    
    print(f"accuracy={avg_score:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents from MinIO to Qdrant via Streaming")
    parser.add_argument("--minio_endpoint", type=str, default="minio-service.kubeflow.svc:9000")
    parser.add_argument("--minio_access_key", type=str, default="minio")
    parser.add_argument("--minio_secret_key", type=str, default="minio123")
    parser.add_argument("--bucket", type=str, required=True)
    parser.add_argument("--prefix", type=str, default="")
    parser.add_argument("--qdrant_host", type=str, default="qdrant.qdrant.svc.cluster.local")
    parser.add_argument("--qdrant_port", type=int, default=6333)
    parser.add_argument("--chunk_size", type=int, default=512)
    parser.add_argument("--chunk_overlap", type=int, default=20)
    parser.add_argument("--splitter_mode", type=str, default="fixed", choices=["fixed", "semantic"])
    parser.add_argument("--breakpoint_threshold", type=int, default=95)
    parser.add_argument("--max_docs", type=int, default=15)
    parser.add_argument("--top_k", type=int, default=3)
    parser.add_argument("--model_name", type=str, default="BAAI/bge-small-en-v1.5")
    parser.add_argument("--cleanup", action="store_true", help="Delete and recreate collection before ingestion")

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
        args.cleanup
    )
