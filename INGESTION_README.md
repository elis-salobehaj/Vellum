# Ingestion Quick Reference

The canonical ingestion guide now lives in `docs/guides/INGESTION_VERIFICATION.md`.

Phase 1 accepted baseline:
- `INGESTION_MODE=direct` is the normal local and cluster-side ingestion path.
- `POST /api/v1/admin/upload-and-ingest` triggers ingestion.
- `GET /api/v1/admin/ingestion-status` reports persisted progress, skipped files, and the last run summary.
- `cleanup=true` performs a clean-slate rebuild.
- `reset_progress=true` restarts scanning from the beginning of the bucket.
- A second direct-ingestion trigger is rejected while another run is already `running`.

Use the full guide for live validation steps, MinIO/Qdrant checks, and the optional `INGESTION_MODE=kfp` workflow.
