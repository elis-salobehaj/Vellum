import hashlib
import io
import json
import os
import shutil
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import qdrant_client
from llama_index.core import Settings, SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from minio import Minio
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    VectorParams,
)

from app.core.config import settings


class DirectIngestionService:
    STATUS_OBJECT_PREFIX = "_vellum/ingestion-status/"
    STATUS_HISTORY_LIMIT = 10

    @staticmethod
    def _build_source_doc_id(file_key: str) -> str:
        return hashlib.sha256(file_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_source_signature(obj: object) -> str:
        etag = getattr(obj, "etag", "") or ""
        size = getattr(obj, "size", 0) or 0
        return f"{etag}:{size}"

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _build_status_object_key(self, bucket: str, prefix: str) -> str:
        scope = f"{bucket}:{prefix.strip('/')}"
        digest = hashlib.sha256(scope.encode("utf-8")).hexdigest()
        return f"{self.STATUS_OBJECT_PREFIX}{digest}.json"

    def _is_status_object(self, object_name: str) -> bool:
        return object_name.startswith(self.STATUS_OBJECT_PREFIX)

    def _load_status(self, minio_client: Minio, bucket: str, prefix: str) -> dict:
        response = None
        try:
            response = minio_client.get_object(
                bucket,
                self._build_status_object_key(bucket, prefix),
            )
            payload = response.read()
            if not payload:
                return {}
            return json.loads(payload.decode("utf-8"))
        except Exception:
            return {}
        finally:
            if response is not None:
                response.close()
                response.release_conn()

    def _save_status(
        self,
        minio_client: Minio,
        bucket: str,
        prefix: str,
        status: dict,
    ) -> None:
        payload = json.dumps(status, sort_keys=True).encode("utf-8")
        minio_client.put_object(
            bucket,
            self._build_status_object_key(bucket, prefix),
            io.BytesIO(payload),
            len(payload),
            content_type="application/json",
        )

    def _append_status_item(self, status: dict, field: str, value: str) -> None:
        items = list(status.get(field, []))
        items.append(value)
        status[field] = items[-self.STATUS_HISTORY_LIMIT :]

    def _list_source_objects(
        self,
        minio_client: Minio,
        bucket: str,
        prefix: str,
    ) -> List[object]:
        objects = list(minio_client.list_objects(bucket, prefix=prefix, recursive=True))
        file_objects = [
            obj
            for obj in objects
            if not obj.is_dir and not self._is_status_object(obj.object_name)
        ]
        file_objects.sort(key=lambda obj: obj.object_name)
        return file_objects

    def _select_batch(
        self,
        file_objects: List[object],
        last_scanned_key: Optional[str],
        batch_size: int,
    ) -> Tuple[List[object], bool, Optional[str], bool]:
        if not file_objects:
            return [], True, None, False

        start_index = 0
        restarted_scan = False
        if last_scanned_key:
            next_index = next(
                (
                    index
                    for index, obj in enumerate(file_objects)
                    if obj.object_name > last_scanned_key
                ),
                None,
            )
            if next_index is None:
                restarted_scan = True
            else:
                start_index = next_index

        if batch_size > 0:
            end_index = min(len(file_objects), start_index + batch_size)
        else:
            end_index = len(file_objects)

        batch = file_objects[start_index:end_index]
        cycle_complete = end_index >= len(file_objects)
        next_resume_key = None if cycle_complete or not batch else batch[-1].object_name
        return batch, cycle_complete, next_resume_key, restarted_scan

    def _count_indexed_source_docs(
        self,
        client: qdrant_client.QdrantClient,
    ) -> int:
        source_doc_ids = set()
        offset = None

        while True:
            response, offset = client.scroll(
                collection_name=settings.QDRANT_COLLECTION,
                limit=256,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            if not response:
                break

            for point in response:
                payload = point.payload or {}
                source_doc_id = payload.get("source_doc_id") or payload.get("doc_id")
                if source_doc_id:
                    source_doc_ids.add(source_doc_id)

            if offset is None:
                break

        return len(source_doc_ids)

    def get_status(self, bucket: str, prefix: str = "") -> dict:
        client = qdrant_client.QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )
        minio_client = Minio(
            settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False,
        )

        file_objects: List[object] = []
        if minio_client.bucket_exists(bucket):
            file_objects = self._list_source_objects(minio_client, bucket, prefix)

        status = self._load_status(minio_client, bucket, prefix)
        indexed_source_docs = 0
        if client.collection_exists(settings.QDRANT_COLLECTION):
            indexed_source_docs = self._count_indexed_source_docs(client)

        total_source_objects = len(file_objects)
        pending_source_objects = max(total_source_objects - indexed_source_docs, 0)

        return {
            "bucket": bucket,
            "prefix": prefix,
            "status": status.get("status", "idle"),
            "current_file": status.get("current_file"),
            "last_scanned_key": status.get("last_scanned_key"),
            "last_completed_key": status.get("last_completed_key"),
            "next_resume_key": status.get("next_resume_key"),
            "last_error": status.get("last_error"),
            "started_at": status.get("started_at"),
            "updated_at": status.get("updated_at"),
            "completed_at": status.get("completed_at"),
            "cycle_complete": status.get("cycle_complete", False),
            "batch_size": status.get("batch_size"),
            "scanned_in_run": status.get("scanned_in_run", 0),
            "indexed_files_in_run": status.get("indexed_files_in_run", 0),
            "indexed_documents_in_run": status.get("indexed_documents_in_run", 0),
            "unchanged_files_in_run": status.get("unchanged_files_in_run", 0),
            "skipped_files_in_run": status.get("skipped_files_in_run", 0),
            "recent_skipped_files": status.get("recent_skipped_files", []),
            "recent_unchanged_files": status.get("recent_unchanged_files", []),
            "last_run_summary": status.get("last_run_summary"),
            "bucket_object_count": total_source_objects,
            "indexed_source_doc_count": indexed_source_docs,
            "pending_source_object_count": pending_source_objects,
            "cleanup_requested": status.get("cleanup_requested", False),
        }

    def _ensure_collection(self, client: qdrant_client.QdrantClient, emit) -> None:
        if client.collection_exists(settings.QDRANT_COLLECTION):
            return

        emit(f"🆕 Creating collection '{settings.QDRANT_COLLECTION}'...")
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    def _get_existing_source_signature(
        self,
        client: qdrant_client.QdrantClient,
        source_doc_id: str,
    ) -> Tuple[bool, Optional[str]]:
        response, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="doc_id",
                        match=MatchValue(value=source_doc_id),
                    )
                ]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False,
        )

        if not response:
            return False, None

        payload = response[0].payload or {}
        return True, payload.get("source_signature")

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
        batch_size: int = 25,
        top_k: int = 2,
        model_name: str = "BAAI/bge-small-en-v1.5",
        reset_progress: bool = False,
    ) -> List[str]:
        logs: List[str] = []

        def emit(message: str) -> None:
            logs.append(message)

        emit("🚀 Running direct ingestion mode...")
        emit(
            f"🔌 Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}"
        )
        client = qdrant_client.QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT,
        )

        if cleanup:
            emit(f"🧹 Resetting collection '{settings.QDRANT_COLLECTION}'...")
            if client.collection_exists(settings.QDRANT_COLLECTION):
                client.delete_collection(settings.QDRANT_COLLECTION)

        self._ensure_collection(client, emit)

        vector_store = QdrantVectorStore(
            client=client,
            collection_name=settings.QDRANT_COLLECTION,
        )

        api_key = settings.OPENAI_API_KEY or "EMPTY"
        Settings.embed_model = OpenAIEmbedding(
            model_name=model_name,
            api_base=settings.EMBEDDINGS_SERVICE_URL,
            api_key=api_key,
            embed_batch_size=4,
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
            emit(f"✂️ Using fixed splitter size {chunk_size} overlap {chunk_overlap}")
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

        file_objects = self._list_source_objects(minio_client, bucket, prefix)
        if max_docs > 0 and len(file_objects) > max_docs:
            file_objects = file_objects[:max_docs]

        if not file_objects:
            raise ValueError(
                f"No files found in bucket '{bucket}' for direct ingestion"
            )

        existing_status = self._load_status(minio_client, bucket, prefix)
        if existing_status.get("status") == "running":
            raise RuntimeError(
                "Direct ingestion is already running for this bucket/prefix; wait for it to finish or pause before triggering another run"
            )

        previous_status = {} if cleanup or reset_progress else existing_status
        batch, cycle_complete, next_resume_key, restarted_scan = self._select_batch(
            file_objects,
            previous_status.get("last_scanned_key"),
            batch_size,
        )

        if restarted_scan:
            emit(
                "🔁 Resume checkpoint reached the end of the source list; restarting from the first file"
            )

        emit(
            f"📂 Evaluating {len(batch)} of {len(file_objects)} files from bucket '{bucket}'"
        )

        status = {
            "bucket": bucket,
            "prefix": prefix,
            "status": "running",
            "current_file": None,
            "last_scanned_key": previous_status.get("last_scanned_key")
            if not restarted_scan
            else None,
            "last_completed_key": previous_status.get("last_completed_key")
            if not restarted_scan
            else None,
            "next_resume_key": previous_status.get("next_resume_key")
            if not restarted_scan
            else None,
            "last_error": None,
            "started_at": self._utc_now(),
            "updated_at": self._utc_now(),
            "completed_at": None,
            "cycle_complete": False,
            "batch_size": batch_size,
            "scanned_in_run": 0,
            "indexed_files_in_run": 0,
            "indexed_documents_in_run": 0,
            "unchanged_files_in_run": 0,
            "skipped_files_in_run": 0,
            "recent_skipped_files": [],
            "recent_unchanged_files": [],
            "last_run_summary": None,
            "total_source_objects": len(file_objects),
            "cleanup_requested": cleanup,
        }
        self._save_status(minio_client, bucket, prefix, status)

        indexed_documents = 0
        indexed_files = 0
        skipped_files: List[str] = []
        unchanged_files: List[str] = []

        try:
            for index, obj in enumerate(batch, start=1):
                file_key = obj.object_name
                emit(f"   🧭 [{index}/{len(batch)}] Processing {file_key}")
                status["current_file"] = file_key
                status["updated_at"] = self._utc_now()
                self._save_status(minio_client, bucket, prefix, status)

                source_doc_id = self._build_source_doc_id(file_key)
                source_signature = self._build_source_signature(obj)
                exists, existing_signature = self._get_existing_source_signature(
                    client, source_doc_id
                )

                if exists and existing_signature == source_signature:
                    unchanged_files.append(file_key)
                    status["scanned_in_run"] += 1
                    status["unchanged_files_in_run"] += 1
                    self._append_status_item(status, "recent_unchanged_files", file_key)
                    status["last_scanned_key"] = file_key
                    status["last_completed_key"] = file_key
                    status["updated_at"] = self._utc_now()
                    self._save_status(minio_client, bucket, prefix, status)
                    emit(f"   ⏭️ Skipping unchanged file: {file_key}")
                    continue

                target_path = os.path.join(temp_dir, file_key)
                os.makedirs(os.path.dirname(target_path), exist_ok=True)

                try:
                    emit(f"   📥 {file_key}")
                    minio_client.fget_object(bucket, file_key, target_path)
                    reader = SimpleDirectoryReader(input_files=[target_path])
                    file_documents = reader.load_data()
                except Exception as exc:
                    skipped_files.append(file_key)
                    status["scanned_in_run"] += 1
                    status["skipped_files_in_run"] += 1
                    self._append_status_item(status, "recent_skipped_files", file_key)
                    status["last_scanned_key"] = file_key
                    status["last_completed_key"] = file_key
                    status["last_error"] = f"{file_key}: {exc}"
                    status["updated_at"] = self._utc_now()
                    self._save_status(minio_client, bucket, prefix, status)
                    emit(f"   ⚠️ Skipping {file_key}: {exc}")
                    continue

                if not file_documents:
                    skipped_files.append(file_key)
                    status["scanned_in_run"] += 1
                    status["skipped_files_in_run"] += 1
                    self._append_status_item(status, "recent_skipped_files", file_key)
                    status["last_scanned_key"] = file_key
                    status["last_completed_key"] = file_key
                    status["last_error"] = f"{file_key}: no supported content extracted"
                    status["updated_at"] = self._utc_now()
                    self._save_status(minio_client, bucket, prefix, status)
                    emit(f"   ⚠️ Skipping {file_key}: no supported content extracted")
                    continue

                for document in file_documents:
                    metadata = dict(document.metadata or {})
                    metadata["source_object_key"] = file_key
                    metadata["source_doc_id"] = source_doc_id
                    metadata["source_signature"] = source_signature
                    metadata["source_etag"] = getattr(obj, "etag", "") or ""
                    metadata["source_size"] = getattr(obj, "size", 0) or 0
                    document.metadata = metadata
                    document.doc_id = source_doc_id

                if exists:
                    emit(f"   ♻️ Replacing existing chunks for: {file_key}")
                    vector_store.delete(source_doc_id)

                pipeline.run(documents=file_documents)
                status["scanned_in_run"] += 1
                status["indexed_files_in_run"] += 1
                status["indexed_documents_in_run"] += len(file_documents)
                status["last_scanned_key"] = file_key
                status["last_completed_key"] = file_key
                status["updated_at"] = self._utc_now()
                self._save_status(minio_client, bucket, prefix, status)
                indexed_files += 1
                indexed_documents += len(file_documents)
        except Exception as exc:
            status["status"] = "failed"
            status["last_error"] = str(exc)
            status["updated_at"] = self._utc_now()
            self._save_status(minio_client, bucket, prefix, status)
            raise

        if indexed_documents == 0 and not unchanged_files:
            status["status"] = "failed"
            status["current_file"] = None
            status["last_error"] = (
                "No supported documents could be loaded from MinIO for direct ingestion"
            )
            status["updated_at"] = self._utc_now()
            self._save_status(minio_client, bucket, prefix, status)
            raise ValueError(
                "No supported documents could be loaded from MinIO for direct ingestion"
            )

        if skipped_files:
            emit(
                f"⚠️ Skipped {len(skipped_files)} unreadable files; continuing with supported documents"
            )

        if unchanged_files:
            emit(f"ℹ️ Skipped {len(unchanged_files)} unchanged files already in Qdrant")

        indexed_source_docs = self._count_indexed_source_docs(client)
        status["status"] = "completed" if cycle_complete else "paused"
        status["current_file"] = None
        status["next_resume_key"] = next_resume_key
        status["cycle_complete"] = cycle_complete
        status["updated_at"] = self._utc_now()
        status["completed_at"] = self._utc_now() if cycle_complete else None
        status["indexed_source_doc_count"] = indexed_source_docs
        status["bucket_object_count"] = len(file_objects)
        status["last_run_summary"] = {
            "indexed_files": indexed_files,
            "indexed_documents": indexed_documents,
            "unchanged_files": len(unchanged_files),
            "skipped_files": len(skipped_files),
            "cycle_complete": cycle_complete,
            "next_resume_key": next_resume_key,
        }
        self._save_status(minio_client, bucket, prefix, status)

        if indexed_documents == 0:
            emit("✅ No new or changed documents to index")
            if cycle_complete:
                emit("✅ Scan cycle complete")
            else:
                emit(f"⏸️ Batch complete; resume after {next_resume_key}")
            return logs

        emit(
            f"🔄 Indexed {indexed_documents} extracted documents from {indexed_files} files into Qdrant"
        )
        emit(
            f"📊 Indexed source docs: {indexed_source_docs}/{len(file_objects)} objects in bucket"
        )
        if cycle_complete:
            emit("✅ Scan cycle complete")
        else:
            emit(f"⏸️ Batch complete; resume after {next_resume_key}")
        emit("✅ Direct ingestion complete")
        return logs


direct_ingestion_service = DirectIngestionService()
