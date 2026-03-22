## Plan Review: [Infrastructure Migration to Kind + Ray-Native Architecture — Phase 4]

**Plan file**: `docs/plans/active/infra-migration.md`
**Reviewed against**: AGENTS.md, docs/context/*, active plans
**Verdict**: 🟢 READY (Remediated)

### Summary

The Phase 4 infrastructure migration successfully integrates Dagster, Istio Ambient Mode, and Entra ID JWT verification, stripping out heavy Kubeflow components and creating a lighter stack. However, the `StorageService` abstraction is bypassed by the `direct_ingestion_service.py`, resulting in an architectural blocker for cloud deployment. Additionally, missing test coverage and failing linter checks prevent the build from passing the `review-plan-phase` quality gates.

**Findings**: 1 BLOCKER · 2 RISK · 0 OPTIMIZATION

---

### BLOCKERs

#### B1: Hardcoded Local Storage in Direct Ingestion
- **Dimension**: Architecture
- **Finding**: Task 4.4 states "Migrate `backend/app/services/direct_ingestion_service.py` — replace hardcoded MinIO with filesystem path", which was done. However, this violates the new `StorageService` abstraction created in Task 4.2. `direct_ingestion_service.py` uses `os.walk` on `settings.DOCUMENT_STORAGE_PATH` directly instead of `storage_service.list_files()` and `storage_service.download()`. This breaks `INGESTION_MODE=direct` entirely when `USE_S3_STORAGE=true`. 
- **Impact**: In a cloud deployment using S3, the backend will crash attempting to index a local directory instead of the configured S3 bucket.
- **Alternative**: Refactor `direct_ingestion_service.py` to use `storage_service.list_files()` and a temporary file sync mechanism using `storage_service.download()` (since Llama Index's `SimpleDirectoryReader` requires valid local file paths) or directly load data from the downloaded stream.

---

### RISKs

#### R1: Linter and Syntax Errors Blocking Build
- **Dimension**: Tests
- **Finding**: Running `uv run ruff check` yields 6 validation errors across:
  - `backend/main.py`: Module level import not at top of file
  - `backend/recreate_collection.py`: Module level import not at top of file
  - `backend/tests/test_services.py`: Unused `datetime` imports and variables
  - `backend/verify_rag_manual.py`: Unused `Citation` import
- **Impact**: Fails the required AGENTS.md build gate (`uv run ruff check`). Breaks CI workflows.
- **Alternative**: Resolve all linting errors by running formatters (`uv run ruff check --fix`) or manually addressing the rogue imports.

#### R2: Missing Test Coverage for New Phase 4 Services
- **Dimension**: Tests
- **Finding**: There is no test coverage for the newly implemented `StorageService` (`backend/app/services/storage_service.py`) nor `DagsterService` (`backend/app/services/dagster_service.py`), though the old minio-dependent bits they replace were removed.
- **Impact**: Key architectural services responsible for fetching cloud data and orchestrating ingestion have zero validation of their expected behavior.
- **Alternative**: Implement `backend/tests/test_storage_service.py` and `backend/tests/test_dagster_service.py` with mock coverage.

---

### Confirmed Strengths

- **Mesh Security**: Istio Ambient Mode `Gateway`, `RequestAuthentication`, and `AuthorizationPolicy` definitions are rock-solid and match the modern zero-trust setup.
- **Auth Enforcement**: The backend correctly stripped out all Dex/`kubeflow-userid` spoofable fallbacks in `auth.py`, shifting solely to Entra ID JWT verification.
- **Pipeline Abstraction**: The Dagster `@asset` definitions natively utilize `StorageResource` configurations, correctly abstracting the S3 vs Local logic out of the execution plan.

### Verdict & Remediation Details

🟢 READY. The phase has been accepted. The Direct Ingestion service adheres to the new `StorageService` abstraction (solving the S3 cloud deploy blocker) and the backend test suite/linters completely pass. 

### Ordered Remediation Steps

- [x] **[agent] Step 1: Fix Linter Constraints**: Address the import path issues in `main.py` and `recreate_collection.py` and remove unused imports in the backend test files.
- [x] **[agent] Step 2: Ensure direct_ingestion_service.py uses StorageService**: Update `_list_source_files` to use `storage_service.list_files()` and dynamically download the needed bytes using `storage_service.download()` before feeding to Llama-Index.
- [x] **[agent] Step 3: Implement new Test Modules**: Add `test_storage_service.py` and `test_dagster_service.py`.

### Required Validations

- [x] Backend: `cd backend && uv run ruff check && uv run pytest -q`
- [x] Frontend: Tests and linters pass (`pnpm test` etc.)
- [x] Documentation references verified (no stale behavior, removed files, or outdated config)
