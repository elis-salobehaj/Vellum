import os
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import qdrant_client
from app.core.config import settings

from llama_index.core.postprocessor.types import BaseNodePostprocessor
from llama_index.core.schema import NodeWithScore, QueryBundle
from typing import List, Optional

class UniqueFilePostprocessor(BaseNodePostprocessor):
    """Keep only the first node for each unique file_name."""
    
    def _postprocess_nodes(
        self, nodes: List[NodeWithScore], query_bundle: Optional[QueryBundle] = None
    ) -> List[NodeWithScore]:
        unique_files = set()
        filtered_nodes = []
        
        for node_with_score in nodes:
            file_name = node_with_score.node.metadata.get("file_name")
            if file_name not in unique_files:
                unique_files.add(file_name)
                filtered_nodes.append(node_with_score)
        
        return filtered_nodes

class RAGService:
    def __init__(self):
        self.client = qdrant_client.QdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.aclient = qdrant_client.AsyncQdrantClient(
            host=settings.QDRANT_HOST,
            port=settings.QDRANT_PORT
        )
        self.vector_store = QdrantVectorStore(
            client=self.client,
            aclient=self.aclient,
            collection_name=settings.QDRANT_COLLECTION
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)

        # Configure Embedding Model (Remote TEI Service)
        # We use OpenAIEmbedding client to talk to our self-hosted Text Embeddings Inference service
        # This removes the need for 'torch' and 'transformers' in the backend.
        Settings.embed_model = OpenAIEmbedding(
            model_name=settings.EMBEDDING_MODEL_NAME,
            api_base=settings.EMBEDDINGS_SERVICE_URL,
            api_key="EMPTY",
            embed_batch_size=30
        )

    async def query(self, query_text: str, k: int = 5):
        """
        Query the RAG system using the remote embedding service and Qdrant.
        """
        index = VectorStoreIndex.from_vector_store(
            self.vector_store,
            storage_context=self.storage_context,
            embed_model=Settings.embed_model
        )

        # 1. Configure retriever for Source Diversity using MMR (Maximal Marginal Relevance)
        retriever = index.as_retriever(
            similarity_top_k=k * 4, 
            vector_store_query_mode="mmr",
            mmr_threshold=0.7
        )
        nodes = await retriever.aretrieve(query_text)
        
        # 2. Apply Postprocessor for Unique Files
        postprocessor = UniqueFilePostprocessor()
        filtered_nodes = postprocessor.postprocess_nodes(nodes)
        
        # 3. Format results (limit to k)
        context = []
        for node in filtered_nodes[:k]:
            context.append({
                "text": node.node.get_text(),
                "metadata": node.node.metadata,
                "score": node.score
            })
            
        return context

rag_service = RAGService()
