# Vellum Backend

The Python FastAPI backend for the Vellum Chatbot.

## Technology Stack
- **Framework**: FastAPI
- **LLM Orchestration**: LlamaIndex
- **Vector DB**: ChromaDB (Persistent)
- **Local LLMs**: Ollama integration
- **Embeddings**: `BAAI/bge-large-en-v1.5` (HuggingFace)

## Key Features
- **RAG Pipeline**: Ingests documents from `data/source_documents` and indexes them.
- **Model Management**: API to plug in different Ollama models (Mistral, Llama 3, Gemma).
- **History Service**: Stores chat sessions.
- **Secure API**: MSAL token validation (optional/configurable).

## Local Development

```bash
# Create venv
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload
```

## Docker Configuration
- **Ollama**: Connects to `kbase-ai-ollama` container.
- **Data Persistence**: Maps `data/` to container volume.
- **Optimization**: `.dockerignore` excludes `venv` to speed up builds.

## API Endpoints
- `GET /api/v1/health`: Health check
- `POST /api/v1/chat`: Chat interaction
- `GET /api/v1/admin/models`: List available LLMs
