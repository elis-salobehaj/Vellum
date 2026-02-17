title: "Phase 6: Advanced RAG Orchestration & Multi-Model Integration"
status: implemented
priority: high
estimated_hours: 40-60
dependencies: []
created: 2026-02-16
date_updated: 2026-02-17
date_completed: 2026-02-17
related_files:
  - backend/pyproject.toml
  - backend/app/core/config.py
  - backend/app/services/llm_service.py
  - backend/app/services/chat_service.py
  - kubeflow/pipelines/ingestion/scripts/run_ingestion.py
  - backend/app/services/rag_service.py
tags:
  - langgraph
  - aws-bedrock
  - openai
  - sota-rag
  - api-embeddings
completion:

  - [x] **1. Infrastructure & Auth**
    - [x] Update `backend/pyproject.toml` with `boto3`, `langchain-aws`, `langchain-openai`, `langgraph`, `langchain`.
    - [x] Update `backend/app/core/config.py` to support `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `OPENAI_API_KEY`.
    - [x] Configure `ModelConfig` schema for AWS Bedrock provider in `backend/app/models/schemas.py`.
    - [x] Verify connectivity to AWS Bedrock and OpenAI APIs via `backend/tests/test_connectivity.py`.
  - [x] **2. LangGraph Implementation**
    - [x] Create `backend/app/graph/` directory with `__init__.py`, `state.py`, `nodes.py`, `graph.py`.
    - [x] Define `GraphState` in `state.py`:
      - `messages`: List[BaseMessage]
      - `documents`: List[Document]
      - `generation`: str
      - `query`: str (for rewriting)
    - [x] Implement Nodes in `nodes.py`:
      - [x] `retrieve`: Fetch documents using `RAGService.query()`.
      - [x] `grade_documents`: LLM-based relevance check (use `gpt-4o-mini` or `claude-3-haiku` for cost).
      - [x] `generate`: Final answer synthesis using the primary model.
      - [x] `transform_query`: Rewrite query if retrieval quality is low.
    - [x] Implement Edges & Workflow in `graph.py`:
      - [x] `decide_to_generate`: Condition to check if Documents are relevant.
      - [x] `grade_generation_v_documents`: Hallucination check.
      - [x] `grade_generation_v_question`: Answer relevance check.
  - [x] **3. SOTA Model Integration**
    - [x] Update `LLMService` to initialize `ChatBedrock` (Claude 3.5 Sonnet) and `ChatOpenAI` (GPT-4o) clients.
    - [x] Configure `ChatBedrock`: `model_id="anthropic.claude-3-5-sonnet-20240620"`.
    - [x] Configure `ChatOpenAI`: `model="gpt-4o"`.
    - [x] Update `LLMService.chat` to route requests to the appropriate LangChain chat model.
  - [x] **4. API-Based Embeddings Integration**
    - [x] **Backend Update**:
      - [x] Modify `backend/app/services/rag_service.py`: Replace `OpenAIEmbedding` (TEI) with `OpenAIEmbedding` using `text-embedding-3-small` (or `ada-002`) and actual OpenAI API Key.
      - [x] Remove `EMBEDDINGS_SERVICE_URL` usage for api-based models.
      - [x] Update `settings.EMBEDDING_MODEL_NAME` default to `text-embedding-3-small`.
    - [x] **Ingestion Pipeline Update**:
      - [x] Modify `kubeflow/pipelines/ingestion/scripts/run_ingestion.py` to accept an API Key for embeddings.
      - [x] Switch `OpenAIEmbedding` init to use `api_key=os.getenv("OPENAI_API_KEY")`.
      - [x] Update `kubeflow/pipelines/ingestion/pipeline.py` to pass the API Key secret to the pod.
    - [x] **Migration Strategy**:
      - [x] Create a script for "Re-Ingestion": Clear Qdrant collection -> Re-run ingestion with new model.
  - [x] **5. Interface Updates**
    - [x] Update `frontend/src/hooks/useModels.ts` (mock or API) to include new models in the selector.
    - [x] Ensure `frontend/src/components/features/chat/ChatInput.tsx` sends the correct `model_id`.
---

# Phase 6: Advanced RAG Orchestration

This phase focuses on upgrading Vellum's reasoning capabilities by integrating **LangGraph** for resilient, agentic RAG workflows and support for State-of-the-Art (SOTA) models via **OpenAI** and **AWS Bedrock**. Additionally, we will transition from self-hosted TEI embeddings to **API-based Embeddings** (OpenAI) for higher quality and reduced operational maintenance.

## 1. Objectives

- **Multi-Provider Support**: Seamlessly switch between OpenAI (GPT-4o), AWS Bedrock (Claude 3.5 Sonnet), and existing models.
- **Agentic RAG**: Replace linear RAG chains with a cyclic **LangGraph** workflow that includes:
  - **Self-Correction**: Grading retrieved documents for relevance.
  - **Query Transformation**: Rewriting queries if retrieval fails.
  - **Hallucination Checks**: Verifying answers against documents.
- **High-Quality Embeddings**: Switch to OpenAI's `text-embedding-3-small` (or similar) for superior retrieval performance compared to locally hosted small models.

## 2. Architecture Changes

### Backend
- **New Dependency Stack**: Introduce `langgraph`, `langchain`, `langchain-aws`, `langchain-openai`.
- **Graph Service**: A new service module (`backend/app/graph`) to handle the stateful execution of RAG workflows.
- **Configuration**: Enhanced `config.py` to securely load AWS and OpenAI credentials.

### Infrastructure (Kubeflow & Ingestion)
- **Ingestion Update**: The ingestion pipeline (`run_ingestion.py`) will be updated to use OpenAI's Embedding API instead of the internal TEI service.
- **Secrets Management**: K8s Secrets for `OPENAI_API_KEY` and AWS credentials must be mounted to both Backend and Ingestion pods.

## 3. Implementation Plan

### Step 1: Foundation & Auth
- Install necessary Python packages.
- Update `pydantic-settings` to handle new credential environment variables.
- Verify connectivity to AWS Bedrock and OpenAI APIs.

### Step 2: LangGraph Core
- Define the `GraphState` schema.
- Implement the "Smart Retriever" node that interacts with Qdrant.
- Implement the "Grader" node using a lightweight LLM (e.g., GPT-4o-mini or Claude Haiku) to filter noise.
- Implement the "Generator" node using the selected primary model.

### Step 3: API-Based Embeddings Migration
- **Stop TEI**: We will deprecate the local TEI service for this phase.
- **Update Backend**: Configure `RagService` to use OpenAI embeddings.
- **Update Ingestion**: Modify the KFP pipeline to use OpenAI embeddings.
- **Re-index**: Run a full re-ingestion of the document corpus using the new embedding model (incompatible with old vectors).

### Step 4: Integration
- Connect the new `GraphService` to the existing `chat` endpoint.
- Ensure streaming responses work with the graph execution.

### Step 5: Verification
- Validate RAG performance on complex queries.
- Benchmark retrieval quality with the new Model.

## 4. Risks & Mitigations

- **Cost**: API-based embeddings and LLM calls incur usage costs.
  - *Mitigation*: Use `text-embedding-3-small` (cheaper) and `gpt-4o-mini` for grading.
- **Ingestion Latency**: API calls during ingestion are slower than local inference.
  - *Mitigation*: The KFP pipeline is already async/batch-optimized, but we may need to adjust batch sizes to avoid rate limits.
