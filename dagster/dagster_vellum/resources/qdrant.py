"""Dagster resource — Qdrant vector store connection."""
from __future__ import annotations

import os

from dagster import ConfigurableResource


class QdrantResource(ConfigurableResource):
    """Thin wrapper around qdrant_client.QdrantClient for Dagster assets."""

    host: str = "qdrant.qdrant.svc.cluster.local"
    port: int = 6333
    collection: str = "vellum"

    def client(self):
        from qdrant_client import QdrantClient  # type: ignore[import-untyped]

        return QdrantClient(host=self.host, port=self.port)


def make_qdrant_resource() -> QdrantResource:
    return QdrantResource(
        host=os.getenv("QDRANT_HOST", "qdrant.qdrant.svc.cluster.local"),
        port=int(os.getenv("QDRANT_PORT", "6333")),
        collection=os.getenv("QDRANT_COLLECTION", "vellum"),
    )
