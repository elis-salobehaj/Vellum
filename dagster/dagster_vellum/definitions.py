"""Dagster Definitions — entry point imported by the Helm chart workspace."""
from dagster import Definitions

from dagster_vellum.assets.ingestion import ingested_documents
from dagster_vellum.resources.qdrant import make_qdrant_resource
from dagster_vellum.resources.storage import make_storage_resource
from dagster_vellum.resources.tei import make_tei_resource
from dagster_vellum.sensors.document_sensor import new_documents_sensor

defs = Definitions(
    assets=[ingested_documents],
    sensors=[new_documents_sensor],
    resources={
        "storage": make_storage_resource(),
        "tei": make_tei_resource(),
        "qdrant": make_qdrant_resource(),
    },
)
