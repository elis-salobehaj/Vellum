import os
from typing import List
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import Settings as LlamaSettings
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
import chromadb
from app.core.config import settings
from app.models.schemas import Citation
from llama_index.core.node_parser import SemanticSplitterNodeParser

# Configure global settings
# Use BAAI/bge-large-en-v1.5 for better embedding performance (fits in 8GB VRAM)
LlamaSettings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-large-en-v1.5")

class RAGService:
    def __init__(self):
        self.index = None
        self.chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        self.chroma_collection = self.chroma_client.get_or_create_collection("kbase_docs")
        self.vector_store = ChromaVectorStore(chroma_collection=self.chroma_collection)
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
        
        # Configure Semantic Chunking
        # Uses the embedding model to find "natural breakpoints" in text
        text_splitter = SemanticSplitterNodeParser(
            buffer_size=1,
            breakpoint_percentile_threshold=95,
            embed_model=LlamaSettings.embed_model
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
                text=node.node.get_content()[:200] + "...", # Truncate for display
                score=node.score
            ))
        return citations

rag_service = RAGService()
