"""Dagster asset — document ingestion pipeline.

Reads documents from storage (PVC or S3), chunks them, embeds them via TEI,
and upserts the resulting vectors into Qdrant. This replaces the KFP ingestion
pipeline that was previously defined in kubeflow/pipelines/ingestion/.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from dagster import asset


CHUNK_SIZE = 512
CHUNK_OVERLAP = 40
SUPPORTED_EXTENSIONS = {".pdf", ".txt", ".md", ".docx", ".html"}


def _doc_id(file_key: str) -> str:
    return hashlib.sha256(file_key.encode()).hexdigest()


def _chunk_text(text: str) -> list[str]:
    """Simple fixed-size chunker with overlap — mirrors the KFP pipeline defaults."""
    step = CHUNK_SIZE - CHUNK_OVERLAP
    words = text.split()
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + CHUNK_SIZE])
        if chunk:
            chunks.append(chunk)
    return chunks


def _extract_text(filepath: str, raw: bytes) -> str:
    """Extract plain text from a document. PDF via pypdf, all others as UTF-8."""
    ext = Path(filepath).suffix.lower()
    if ext == ".pdf":
        try:
            from pypdf import PdfReader  # type: ignore[import-untyped]

            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        except Exception:
            return raw.decode("utf-8", errors="ignore")
    return raw.decode("utf-8", errors="ignore")


@asset(
    description="Ingest documents → chunk → embed via TEI → upsert into Qdrant",
    group_name="ingestion",
    required_resource_keys={"storage", "tei", "qdrant"},
)
def ingested_documents(context) -> dict:
    storage = context.resources.storage
    tei = context.resources.tei
    qdrant = context.resources.qdrant
    from qdrant_client.http.models import Distance, PointStruct, VectorParams

    client = qdrant.client()
    collection = qdrant.collection

    # Ensure collection exists — dimension from TEI first probe
    context.log.info(f"Checking Qdrant collection '{collection}'")
    files = storage.list_files()
    context.log.info(f"Found {len(files)} files in storage")

    if not files:
        context.log.warning("No documents found in storage — nothing to ingest")
        return {"doc_count": 0, "chunk_count": 0}

    # Bootstrap collection on first run
    if not client.collection_exists(collection):
        # Probe embedding dimension from a dummy call
        probe_dim = len(tei.embed(["probe"])[0])
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=probe_dim, distance=Distance.COSINE),
        )
        context.log.info(f"Created collection '{collection}' dim={probe_dim}")

    doc_count = 0
    chunk_count = 0

    for file_key in files:
        ext = Path(file_key).suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            context.log.debug(f"Skipping unsupported file type: {file_key}")
            continue

        raw = storage.read_bytes(file_key)
        text = _extract_text(file_key, raw)
        chunks = _chunk_text(text)
        if not chunks:
            context.log.debug(f"No text extracted from {file_key}")
            continue

        embeddings = tei.embed(chunks)
        points = [
            PointStruct(
                id=abs(hash(f"{file_key}:{i}")) % (2**63),
                vector=vec,
                payload={
                    "source": file_key,
                    "doc_id": _doc_id(file_key),
                    "chunk_index": i,
                    "text": chunk,
                },
            )
            for i, (chunk, vec) in enumerate(zip(chunks, embeddings))
        ]
        client.upsert(collection_name=collection, points=points)
        context.log.info(f"Ingested {file_key}: {len(points)} chunks")
        doc_count += 1
        chunk_count += len(points)

    context.log.info(f"Ingestion complete: {doc_count} docs, {chunk_count} chunks")
    return {"doc_count": doc_count, "chunk_count": chunk_count}
