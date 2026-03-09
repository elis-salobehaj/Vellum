import os
import shutil
from typing import List

import qdrant_client
from llama_index.core import Settings, SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from minio import Minio
from qdrant_client.http.models import Distance, VectorParams

from app.core.config import settings


class DirectIngestionService:
    def run(
        self,
        bucket: str,
        prefix: str = "",
        cleanup: bool = False,
        chunk_size: int = 512,
        chunk_overlap: int = 40,
        splitter_mode: str = "fixed",
        breakpoint_threshold: int = 95,
        max_docs: int = 1000,
        top_k: int = 2,
        model_name: str = "BAAI/bge-small-en-v1.5",
    ) -> List[str]:
        logs: List[str] = []

        def emit(message: str) -> None:
            logs.append(message)

        emit("🚀 Running direct ingestion mode...")
        emit(f"🔌 Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
        client = qdrant_client.QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

        if cleanup:
            emit(f"🧹 Resetting collection '{settings.QDRANT_COLLECTION}'...")
            if client.collection_exists(settings.QDRANT_COLLECTION):
                client.delete_collection(settings.QDRANT_COLLECTION)
            client.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=settings.QDRANT_COLLECTION,
        )

        api_key = settings.OPENAI_API_KEY or "EMPTY"
        Settings.embed_model = OpenAIEmbedding(
            model_name=model_name,
            api_base=settings.EMBEDDINGS_SERVICE_URL,
            api_key=api_key,
            embed_batch_size=30,
        )
        emit(f"⚙️ Using embeddings endpoint {settings.EMBEDDINGS_SERVICE_URL}")

        if splitter_mode == "semantic":
            emit(f"✂️ Using semantic splitter threshold {breakpoint_threshold}")
            text_splitter = SemanticSplitterNodeParser(
                buffer_size=1,
                breakpoint_percentile_threshold=breakpoint_threshold,
                embed_model=Settings.embed_model,
            )
        else:
            emit(
                f"✂️ Using fixed splitter size {chunk_size} overlap {chunk_overlap}"
            )
            text_splitter = SentenceSplitter(
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )

        pipeline = IngestionPipeline(
            transformations=[text_splitter, Settings.embed_model],
            vector_store=vector_store,
        )

        emit(f"📡 Connecting to MinIO at {settings.MINIO_ENDPOINT}")
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

        temp_dir = "/tmp/vellum-direct-ingest"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        objects = minio_client.list_objects(bucket, prefix=prefix, recursive=True)
        files = [obj.object_name for obj in objects if not obj.is_dir]
        files.sort()
        if max_docs > 0 and len(files) > max_docs:
            files = files[:max_docs]

        if not files:
            raise ValueError(f"No files found in bucket '{bucket}' for direct ingestion")

        emit(f"📂 Downloading {len(files)} files from bucket '{bucket}'")
        for file_key in files:
            target_path = os.path.join(temp_dir, os.path.basename(file_key))
            emit(f"   📥 {file_key}")
            minio_client.fget_object(bucket, file_key, target_path)

        reader = SimpleDirectoryReader(input_dir=temp_dir)
        documents = reader.load_data()
        emit(f"🔄 Indexing {len(documents)} documents into Qdrant")
        pipeline.run(documents=documents)
        emit("✅ Direct ingestion complete")
        return logs


direct_ingestion_service = DirectIngestionService()