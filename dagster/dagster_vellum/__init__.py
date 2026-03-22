"""Dagster ingestion pipeline for Vellum.

Entry point: dagster_vellum/definitions.py

Project layout:
    dagster_vellum/
    ├── __init__.py
    ├── definitions.py       — Dagster Definitions (imported by Helm chart)
    ├── assets/
    │   └── ingestion.py     — @asset for chunk → embed → upsert
    ├── resources/
    │   ├── storage.py       — document reader (PVC or S3 via USE_S3_STORAGE)
    │   ├── qdrant.py        — Qdrant resource
    │   └── tei.py           — TEI embeddings resource
    └── sensors/
        └── document_sensor.py — trigger ingestion when new documents arrive
"""
