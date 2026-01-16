import os
from typing import List
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.core import Settings as LlamaSettings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import qdrant_client
from app.core.config import settings
from app.models.schemas import Citation


# Configure global settings
# Configure global settings
# Use BAAI/bge-small-en-v1.5 (Tuned Winner: 512/40)
LlamaSettings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")

class RAGService:
    def __init__(self):
        self.index = None
        # Use Qdrant Client (Remote Service)
        self.client = qdrant_client.QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
        self.vector_store = QdrantVectorStore(client=self.client, collection_name="vellum_vectors")
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
    async def ingest_documents(self, source_dir: str):
        """
        Ingest documents from the directory using LlamaIndex.
        Uses Semantic Chunking for context-aware splitting.
        Supports: .pdf, .txt, .md, .docx
        """
        if not os.path.exists(source_dir):
            return {"status": "error", "message": "Directory not found"}
            
        reader = SimpleDirectoryReader(
            input_dir=source_dir, 
            recursive=True, 
            required_exts=[".pdf", ".txt", ".md", ".docx"]
        )
        documents = reader.load_data()
        
        # Configure Fixed Splitter (Optimized via Katib: 512/40)
        from llama_index.core.node_parser import SentenceSplitter
        text_splitter = SentenceSplitter(
            chunk_size=512,
            chunk_overlap=40
        )
        
        # Create index from documents with explicit transformations
        self.index = VectorStoreIndex.from_documents(
            documents, 
            storage_context=self.storage_context,
            transformations=[text_splitter]
        )
        
        return {"status": "success", "count": len(documents)}

    async def query(self, question: str, k: int = 3) -> List[Citation]:
        if not self.index:
            # Try to load if exists
            try:
                self.index = VectorStoreIndex.from_vector_store(
                    self.vector_store, storage_context=self.storage_context
                )
            except Exception as e:
                print(f"ERROR: Failed to load index from storage: {e}", flush=True)
                return []
             
        # Retrieve nodes
        retriever = self.index.as_retriever(similarity_top_k=k)
        nodes = retriever.retrieve(question)
        
        citations = []
        for node in nodes:
            citations.append(Citation(
                source=node.metadata.get("file_name", "unknown"),
                page=int(node.metadata.get("page_label", 0)) if node.metadata.get("page_label") else 0,
                text=node.node.get_content(), # Return full text for LLM Context
                score=node.score
            ))
        return citations

rag_service = RAGService()
