import sys
from unittest.mock import MagicMock, Mock, AsyncMock
import os

# Set test environment headers
os.environ["BYPASS_AUTH"] = "True"
os.environ["OPENAI_API_KEY"] = "dummy"
# Only set defaults if not present (allows running in K8s pod)
if "QDRANT_HOST" not in os.environ:
    os.environ["QDRANT_HOST"] = "localhost"
if "QDRANT_PORT" not in os.environ:
    os.environ["QDRANT_PORT"] = "6333"

# Force mock heavy libraries to avoid model downloads during tests
# We need to handle LlamaIndex type checks for embeddings
try:
    from llama_index.core.base.embeddings.base import BaseEmbedding
    class MockEmbedding(BaseEmbedding):
        def _get_query_embedding(self, query): return []
        def _get_text_embedding(self, text): return []
        async def _aget_query_embedding(self, query): return []
        async def _aget_text_embedding(self, text): return []
except ImportError:
    MockEmbedding = MagicMock

HEAVY_LIBS = [
    # "llama_index.embeddings.openai", # Handled manually below
    "sentence_transformers",
    "chromadb",
    "torch"
]

for lib in HEAVY_LIBS:
    sys.modules[lib] = MagicMock()

# Mock OpenAIEmbedding specifically to pass isinstance checks
mock_openai_module = MagicMock()
mock_openai_module.OpenAIEmbedding = MockEmbedding
sys.modules["llama_index.embeddings.openai"] = mock_openai_module

# Mock HuggingFaceEmbedding specifically to pass isinstance checks
mock_hf_module = MagicMock()
mock_hf_module.HuggingFaceEmbedding = MockEmbedding
sys.modules["llama_index.embeddings.huggingface"] = mock_hf_module

# Mock Qdrant clients to prevent connection attempts in CI
# Mock Qdrant clients locally to prevent connection attempts in CI
# We patch the class functionality without breaking the package structure
import qdrant_client
mock_client = MagicMock()
mock_client.collection_exists.return_value = True

# Patch the classes directly so usage anywhere in the app gets the mock
qdrant_client.QdrantClient = Mock(return_value=mock_client)
qdrant_client.AsyncQdrantClient = Mock(return_value=mock_client)
