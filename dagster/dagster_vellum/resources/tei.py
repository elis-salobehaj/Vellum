"""Dagster resource — TEI (Text Embeddings Inference) embeddings service."""
from __future__ import annotations

import os

import httpx
from dagster import ConfigurableResource


class TEIResource(ConfigurableResource):
    """Calls the TEI service to embed a list of text chunks."""

    service_url: str = "http://embeddings-service.kubeflow-vellum.svc.cluster.local/v1"
    model_name: str = "BAAI/bge-small-en-v1.5"

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Return a list of embedding vectors for the given text inputs."""
        response = httpx.post(
            f"{self.service_url}/embeddings",
            json={"model": self.model_name, "input": texts},
            timeout=60.0,
        )
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]


def make_tei_resource() -> TEIResource:
    return TEIResource(
        service_url=os.getenv(
            "EMBEDDINGS_SERVICE_URL",
            "http://embeddings-service.kubeflow-vellum.svc.cluster.local/v1",
        ),
        model_name=os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5"),
    )
