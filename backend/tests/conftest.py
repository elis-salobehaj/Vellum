import sys
from unittest.mock import MagicMock

# List of heavy libraries to mock if not present
HEAVY_LIBS = [
    "llama_index",
    "llama_index.core",
    "llama_index.vector_stores.chroma",
    "llama_index.embeddings.openai",
    "llama_index.embeddings.huggingface",
    "llama_index.llms.ollama",
    "llama_index.llms.gemini",
    "llama_index.llms.openai",
    "llama_index.core.node_parser",
    "huggingface_hub",
    "sentence_transformers",
    "chromadb",
    "pypdf",
    "torch"
]

for lib in HEAVY_LIBS:
    try:
        __import__(lib)
    except ImportError:
        # Only mock if the library is missing (e.g. in CI with requirements-test.txt)
        sys.modules[lib] = MagicMock()
        print(f"⚠️ Mocking missing library: {lib}")
