"""Direct ingestion service — PVC / local filesystem edition.

Reads documents from DOCUMENT_STORAGE_PATH (local PVC mount or a local
directory in hybrid dev mode). Replaces the previous MinIO-backed version.

Status is persisted to a JSON sidecar at:
    <DOCUMENT_STORAGE_PATH>/.vellum/ingestion-status-<hash>.json
"""
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import qdrant_client
from llama_index.core import Settings, SimpleDirectoryReader
from llama_index.core.ingestion import IngestionPipeline
from llama_index.core.node_parser import SentenceSplitter, SemanticSplitterNodeParser
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchValue,
    VectorParams,
)

from app.core.config import settings
from app.services.storage_service import storage_service

class DirectIngestionService:
    STATUS_DIR_NAME = ".vellum"
    STATUS_HISTORY_LIMIT = 10

    # ── helpers ────────────────────────────────────────────────────────────────

    @staticmethod
    def _build_source_doc_id(file_key: str) -> str:
        return hashlib.sha256(file_key.encode("utf-8")).hexdigest()

    @staticmethod
    def _build_source_signature(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()

    @staticmethod
    def _utc_now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def _status_file(self, base_path: str) -> str:
        digest = hashlib.sha256(base_path.encode()).hexdigest()[:16]
        status_dir = os.path.join(base_path, self.STATUS_DIR_NAME)
        os.makedirs(status_dir, exist_ok=True)
        return os.path.join(status_dir, f"status-{digest}.json")

    def _load_status(self, base_path: str, *_args) -> dict:
        path = self._status_file(base_path)
        if not os.path.exists(path):
            return {}
        try:
            with open(path) as fh:
                return json.load(fh)
        except Exception:
            return {}

    def _save_status(self, base_path: str, *_args, status: dict) -> None:
        path = self._status_file(base_path)
        with open(path, "w") as fh:
            json.dump(status, fh, sort_keys=True, indent=2)

    def _append_status_item(self, status: dict, field: str, value: str) -> None:
        items = list(status.get(field, []))
        items.append(value)
        status[field] = items[-self.STATUS_HISTORY_LIMIT:]

    # ── file listing ──────────────────────────────────────────────────────────

    async def _list_source_files(self, base_path: str) -> List[str]:
        """Return sorted list of file keys from the storage wrapper."""
        raw_files = await storage_service.list_files()
        result = [f for f in raw_files if not f.startswith(self.STATUS_DIR_NAME + "/")]
        result.sort()
        return result

    def _select_batch(
        self,
        file_paths: List[str],
        last_scanned_key: Optional[str],
        batch_size: int,
    ) -> Tuple[List[str], bool, Optional[str], bool]:
        if not file_paths:
            return [], True, None, False

        start_index = 0
        restarted_scan = False
        if last_scanned_key:
            next_index = next(
                (i for i, p in enumerate(file_paths) if p > last_scanned_key),
                None,
            )
            if next_index is None:
                restarted_scan = True
            else:
                start_index = next_index

        end_index = min(len(file_paths), start_index + batch_size) if batch_size > 0 else len(file_paths)
        batch = file_paths[start_index:end_index]
        cycle_complete = end_index >= len(file_paths)
        next_resume_key = None if cycle_complete or not batch else batch[-1]
        return batch, cycle_complete, next_resume_key, restarted_scan

    # ── Qdrant helpers ────────────────────────────────────────────────────────

    def _count_indexed_source_docs(self, client: qdrant_client.QdrantClient) -> int:
        source_doc_ids: set = set()
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

    def _get_existing_source_signature(
        self, client: qdrant_client.QdrantClient, source_doc_id: str
    ) -> Tuple[bool, Optional[str]]:
        response, _ = client.scroll(
            collection_name=settings.QDRANT_COLLECTION,
            scroll_filter=Filter(
                must=[FieldCondition(key="doc_id", match=MatchValue(value=source_doc_id))]
            ),
            limit=1,
            with_payload=True,
            with_vectors=False,
        )
        if not response:
            return False, None
        payload = response[0].payload or {}
        return True, payload.get("source_signature")

    def _ensure_collection(self, client: qdrant_client.QdrantClient, emit) -> None:
        if client.collection_exists(settings.QDRANT_COLLECTION):
            return
        emit(f"🆕 Creating collection '{settings.QDRANT_COLLECTION}'...")
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )

    # ── public API ────────────────────────────────────────────────────────────

    async def get_status(self, *_args, **_kwargs) -> dict:
        base_path = settings.DOCUMENT_STORAGE_PATH
        client = qdrant_client.QdrantClient(
            host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
        )
        file_paths = await self._list_source_files(base_path)
        status = self._load_status(base_path)
        indexed_source_docs = 0
        if client.collection_exists(settings.QDRANT_COLLECTION):
            indexed_source_docs = self._count_indexed_source_docs(client)

        total = len(file_paths)
        return {
            "storage_path": base_path,
            "status": status.get("status", "idle"),
            "current_file": status.get("current_file"),
            "last_error": status.get("last_error"),
            "started_at": status.get("started_at"),
            "updated_at": status.get("updated_at"),
            "cycle_complete": status.get("cycle_complete", False),
            "recent_skipped_files": status.get("recent_skipped_files", []),
            "last_run_summary": status.get("last_run_summary"),
            "total_doc_count": total,
            "indexed_source_doc_count": indexed_source_docs,
        }

    async def run(
        self,
        *_args,
        cleanup: bool = False,
        chunk_size: int = 512,
        chunk_overlap: int = 40,
        splitter_mode: str = "fixed",
        breakpoint_threshold: int = 95,
        max_docs: int = 1000,
        batch_size: int = 25,
        model_name: str = "BAAI/bge-small-en-v1.5",
        reset_progress: bool = False,
        **_kwargs,
    ) -> List[str]:
        base_path = settings.DOCUMENT_STORAGE_PATH
        logs: List[str] = []

        def emit(msg: str) -> None:
            logs.append(msg)

        emit("🚀 Running direct ingestion mode...")
        emit(f"📂 Reading documents using StorageService (S3={settings.USE_S3_STORAGE})")
        emit(f"🔌 Connecting to Qdrant at {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")

        client = qdrant_client.QdrantClient(
            host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
        )

        if cleanup:
            emit(f"🧹 Resetting collection '{settings.QDRANT_COLLECTION}'...")
            if client.collection_exists(settings.QDRANT_COLLECTION):
                client.delete_collection(settings.QDRANT_COLLECTION)

        self._ensure_collection(client, emit)

        vector_store = QdrantVectorStore(
            client=client, collection_name=settings.QDRANT_COLLECTION
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
            text_splitter = SemanticSplitterNodeParser(
                buffer_size=1,
                breakpoint_percentile_threshold=breakpoint_threshold,
                embed_model=Settings.embed_model,
            )
        else:
            text_splitter = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        pipeline = IngestionPipeline(
            transformations=[text_splitter, Settings.embed_model],
            vector_store=vector_store,
        )

        file_paths = await self._list_source_files(base_path)
        if max_docs > 0 and len(file_paths) > max_docs:
            file_paths = file_paths[:max_docs]

        if not file_paths:
            raise ValueError("No files found in storage wrapper for direct ingestion")

        existing_status = self._load_status(base_path)
        if existing_status.get("status") == "running":
            raise RuntimeError(
                "Direct ingestion is already running; wait for it to finish before triggering another run"
            )

        previous_status = {} if cleanup or reset_progress else existing_status
        batch, cycle_complete, next_resume_key, restarted_scan = self._select_batch(
            file_paths,
            previous_status.get("last_scanned_key"),
            batch_size,
        )

        if restarted_scan:
            emit("🔁 Resume checkpoint reached end; restarting from first file")

        emit(f"📂 Evaluating {len(batch)} of {len(file_paths)} files")

        status: dict = {
            "storage_path": base_path,
            "status": "running",
            "current_file": None,
            "last_scanned_key": previous_status.get("last_scanned_key") if not restarted_scan else None,
            "last_completed_key": previous_status.get("last_completed_key") if not restarted_scan else None,
            "next_resume_key": previous_status.get("next_resume_key") if not restarted_scan else None,
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
            "total_source_objects": len(file_paths),
            "cleanup_requested": cleanup,
        }
        self._save_status(base_path, status=status)

        indexed_documents = 0
        indexed_files = 0
        skipped_files: List[str] = []
        unchanged_files: List[str] = []

        temp_dir = "/tmp/vellum-direct-ingest"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)

        try:
            for index, file_key in enumerate(batch, start=1):
                emit(f"   🧭 [{index}/{len(batch)}] Processing {file_key}")
                status["current_file"] = file_key
                status["updated_at"] = self._utc_now()
                self._save_status(base_path, status=status)

                source_doc_id = self._build_source_doc_id(file_key)
                exists, existing_signature = self._get_existing_source_signature(client, source_doc_id)

                try:
                    # Download bytes from storage_service to temp file
                    ext = os.path.splitext(file_key)[1]
                    with tempfile.NamedTemporaryFile(delete=False, suffix=ext, dir=temp_dir) as tmp:
                        content_bytes = bytearray()
                        async for chunk in storage_service.download(file_key):
                            tmp.write(chunk)
                            content_bytes.extend(chunk)
                        tmp_path = tmp.name

                    source_signature = self._build_source_signature(content_bytes)
                except Exception as exc:
                    skipped_files.append(file_key)
                    status["scanned_in_run"] += 1
                    status["skipped_files_in_run"] += 1
                    self._append_status_item(status, "recent_skipped_files", file_key)
                    status["last_scanned_key"] = file_key
                    status["last_completed_key"] = file_key
                    status["last_error"] = f"{file_key}: {exc}"
                    status["updated_at"] = self._utc_now()
                    self._save_status(base_path, status=status)
                    emit(f"   ⚠️ Skipping {file_key}: {exc}")
                    continue

                if exists and existing_signature == source_signature:
                    os.unlink(tmp_path)
                    unchanged_files.append(file_key)
                    status["scanned_in_run"] += 1
                    status["unchanged_files_in_run"] += 1
                    self._append_status_item(status, "recent_unchanged_files", file_key)
                    status["last_scanned_key"] = file_key
                    status["last_completed_key"] = file_key
                    status["updated_at"] = self._utc_now()
                    self._save_status(base_path, status=status)
                    emit(f"   ⏭️ Skipping unchanged file: {file_key}")
                    continue

                try:
                    reader = SimpleDirectoryReader(input_files=[tmp_path])
                    file_documents = reader.load_data()
                except Exception as exc:
                    os.unlink(tmp_path)
                    skipped_files.append(file_key)
                    status["scanned_in_run"] += 1
                    status["skipped_files_in_run"] += 1
                    self._append_status_item(status, "recent_skipped_files", file_key)
                    status["last_scanned_key"] = file_key
                    status["last_completed_key"] = file_key
                    status["last_error"] = f"{file_key}: {exc}"
                    status["updated_at"] = self._utc_now()
                    self._save_status(base_path, status=status)
                    emit(f"   ⚠️ Skipping {file_key}: {exc}")
                    continue
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

                if not file_documents:
                    skipped_files.append(file_key)
                    status["scanned_in_run"] += 1
                    status["skipped_files_in_run"] += 1
                    self._append_status_item(status, "recent_skipped_files", file_key)
                    status["last_scanned_key"] = file_key
                    status["last_completed_key"] = file_key
                    status["last_error"] = f"{file_key}: no supported content extracted"
                    status["updated_at"] = self._utc_now()
                    self._save_status(base_path, status=status)
                    emit(f"   ⚠️ Skipping {file_key}: no supported content extracted")
                    continue

                for document in file_documents:
                    metadata = dict(document.metadata or {})
                    metadata["source_object_key"] = file_key
                    metadata["source_doc_id"] = source_doc_id
                    metadata["source_signature"] = source_signature
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
                self._save_status(base_path, status=status)
                indexed_files += 1
                indexed_documents += len(file_documents)

                if batch_size > 0 and indexed_files >= batch_size:
                    emit(f"⏸️ Batch complete; resume after {file_key}")

        except Exception as exc:
            status["status"] = "failed"
            status["last_error"] = str(exc)
            status["updated_at"] = self._utc_now()
            self._save_status(base_path, status=status)
            raise

        if indexed_documents == 0 and not unchanged_files:
            status["status"] = "failed"
            status["current_file"] = None
            status["last_error"] = "No supported documents could be loaded from storage for direct ingestion"
            status["updated_at"] = self._utc_now()
            self._save_status(base_path, status=status)
            raise ValueError("No supported documents could be loaded from storage for direct ingestion")

        if skipped_files:
            emit(f"⚠️ Skipped {len(skipped_files)} unreadable files")

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
        status["total_source_objects"] = len(file_paths)
        status["last_run_summary"] = {
            "indexed_files": indexed_files,
            "indexed_documents": indexed_documents,
            "unchanged_files": len(unchanged_files),
            "skipped_files": len(skipped_files),
            "cycle_complete": cycle_complete,
            "next_resume_key": next_resume_key,
        }
        self._save_status(base_path, status=status)

        if indexed_documents == 0:
            emit("✅ No new or changed documents to index")
            if cycle_complete:
                emit("✅ Scan cycle complete")
            else:
                emit(f"⏸️ Batch complete; resume after {next_resume_key}")
            return logs

        emit(f"🔄 Indexed {indexed_documents} extracted documents from {indexed_files} files into Qdrant")
        emit(f"📊 Indexed source docs: {indexed_source_docs}/{len(file_paths)} total files")
        if cycle_complete:
            emit("✅ Scan cycle complete")
        else:
            emit(f"⏸️ Batch complete; resume after {next_resume_key}")
        emit("✅ Direct ingestion complete")
        return logs

direct_ingestion_service = DirectIngestionService()
