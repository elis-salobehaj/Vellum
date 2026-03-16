# Historical Note: Older MinIO Model Management Flow

This document is retained for historical context only.

Completed Phase 1 no longer uses MinIO to distribute local LLM model files. The current KServe path downloads models directly from Hugging Face into the shared `llm-models-pvc` via `deployment/model-downloader-job.yaml`, and `deployment/llm-service.yaml` mounts that PVC directly.

What to do now:
- For the current local Qwen model, run the existing deploy/bootstrap flow and let the model downloader job populate the shared PVC.
- If you need to change the shipped local model in the retained Phase 1 stack, update `deployment/model-downloader-job.yaml` and `deployment/llm-service.yaml` together.
- MinIO remains part of Phase 1 for source-document ingestion, not for model artifact distribution.

If a future phase reintroduces object-storage-backed model distribution, replace this note with an up-to-date operational guide instead of reviving the older MinIO instructions verbatim.
