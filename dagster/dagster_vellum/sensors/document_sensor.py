"""Dagster sensor — watches for new documents and triggers ingestion.

Polls the document store on every tick. When new files appear since the last
run, it yields a RunRequest to materialise the `ingested_documents` asset.

Works for both local PVC paths and S3 (the storage resource abstracts this).
"""
from __future__ import annotations

from dagster import RunRequest, SensorEvaluationContext, asset_sensor

from dagster_vellum.assets.ingestion import ingested_documents
from dagster_vellum.resources.storage import make_storage_resource


@asset_sensor(asset_key=ingested_documents.key, minimum_interval_seconds=30)
def new_documents_sensor(
    context: SensorEvaluationContext,
) -> RunRequest | None:
    """Trigger a re-run of `ingested_documents` whenever the document list changes."""
    storage = make_storage_resource()
    current_files: set[str] = set(storage.list_files())

    last_seen_raw: str = context.cursor or ""
    last_seen: set[str] = set(last_seen_raw.split(",")) if last_seen_raw else set()

    new_files = current_files - last_seen
    if not new_files:
        return None  # no change — skip

    context.log.info(f"New documents detected: {new_files}")
    context.update_cursor(",".join(sorted(current_files)))
    return RunRequest(run_key=",".join(sorted(new_files)))
