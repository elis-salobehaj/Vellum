# Ingestion Verification Guide

After triggering **Upload & Ingest**, verify both the source objects and the live ingestion status.

This is the accepted Phase 1 ingestion workflow. Use the direct-ingestion checks below for normal operations on Kind, and only use the KFP section when you are intentionally validating the retained Kubeflow path.

## 1. Verify Source Objects in MinIO
Documents should be present in the `documents` bucket.
- **URL**: [MinIO Console](http://localhost:9000) via `./scripts/connect.sh`
- **Credentials**: `minio` / `minio123`
- **Check**: Browse the `documents` bucket and confirm the expected files are present.

## 2. Verify Direct Ingestion Status
Phase 1 defaults to `INGESTION_MODE=direct`, so the backend ingests from MinIO straight into Qdrant and persists progress in MinIO.

Query the status endpoint:

```bash
curl http://localhost:8006/api/v1/admin/ingestion-status \
	-H "kubeflow-userid: vellum@example.com" | jq
```

Key fields to watch:
- `status`: `running`, `paused`, `completed`, or `failed`
- `current_file`: the file currently being processed
- `last_scanned_key`: the last file evaluated in the current scan order
- `indexed_source_doc_count` vs `bucket_object_count`: unique indexed source docs versus source objects in MinIO
- `recent_skipped_files`: files that loaded as unreadable or empty in the latest run
- `last_run_summary`: the last batch summary including indexed, unchanged, and skipped file counts

Trigger flags:
- `cleanup=true`: delete and recreate the Qdrant collection before the run. Use this when you intentionally want a clean slate and do not want to preserve any existing chunks.
- `reset_progress=true`: ignore the saved `last_scanned_key` checkpoint and start scanning the bucket from the beginning again. Use this when you want to rescan from the top without necessarily wiping the collection.
- `cleanup=true` already implies fresh-scan behavior in the current implementation, so pairing it with `reset_progress=true` is explicit but not strictly required.

Interpretation:
- If `status=running`, do not trigger another ingestion yet. The backend now rejects concurrent direct-ingestion runs for the same bucket/prefix because overlapping runs can make progress reporting misleading.
- If `status=paused`, rerun `/api/v1/admin/upload-and-ingest` to continue the next bounded batch.
- If `cycle_complete=true` and `pending_source_object_count>0`, inspect `recent_skipped_files` first.
- If you want a full rebuild, pass `cleanup=true&reset_progress=true`; otherwise the default path skips unchanged files and replaces chunks only for changed files.

## 3. Verify Qdrant
Direct ingestion writes into the `vellum` collection in Qdrant.
- **URL**: [Qdrant Dashboard](http://localhost:6333/dashboard)
- **Check**: Verify the collection has vectors and that unique source-doc coverage is increasing toward the MinIO object count.

You can also verify via CLI:

```bash
uv run scripts/verify_retrieval.py
```

## 4. Verify KFP Only When Needed
If you explicitly set `INGESTION_MODE=kfp`, also verify the Kubeflow run.
- **URL**: [Kubeflow Dashboard](http://localhost:8086/_/pipeline/#/runs)
- **Check**: Look for a run starting with `ingest-` in the `kubeflow-vellum` namespace.
- **Status**: Should transition to `Succeeded`.

## 5. Test Chat
Once ingestion succeeds, ask a question about the uploaded documents in the main chat page and confirm citations are returned.

## See Also
- [Ingestion Pipeline Architecture](../designs/ingestion-pipeline.md) — Full architecture details
- [Development Guide](DEVELOPMENT.md) — Ingestion commands and troubleshooting
