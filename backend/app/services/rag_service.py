from llama_index.core import VectorStoreIndex, StorageContext
from llama_index.vector_stores.qdrant import QdrantVectorStore
from llama_index.embeddings.openai import OpenAIEmbedding
import qdrant_client
from qdrant_client.http.exceptions import UnexpectedResponse
from app.core.config import settings
from app.core.logging import logger

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
        self._client = None
        self._aclient = None
        self._vector_store = None
        self._storage_context = None

    @property
    def client(self):
        if self._client is None:
            self._client = qdrant_client.QdrantClient(
                host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
            )
        return self._client

    @property
    def aclient(self):
        if self._aclient is None:
            self._aclient = qdrant_client.AsyncQdrantClient(
                host=settings.QDRANT_HOST, port=settings.QDRANT_PORT
            )
        return self._aclient

    @property
    def vector_store(self):
        if self._vector_store is None:
            self._vector_store = QdrantVectorStore(
                client=self.client,
                aclient=self.aclient,
                collection_name=settings.QDRANT_COLLECTION,
            )
        return self._vector_store

    @property
    def storage_context(self):
        if self._storage_context is None:
            self._storage_context = StorageContext.from_defaults(
                vector_store=self.vector_store
            )
        return self._storage_context

    def _get_embed_model(self):
        # The local TEI service exposes an OpenAI-compatible embeddings API.
        return OpenAIEmbedding(
            model_name=settings.EMBEDDING_MODEL_NAME,
            api_base=settings.EMBEDDINGS_SERVICE_URL,
            api_key=settings.OPENAI_API_KEY or "EMPTY",
            embed_batch_size=30,
        )

    async def query(self, query_text: str, k: int = 5):
        """
        Query the RAG system using the remote embedding service and Qdrant.
        """
        logger.info("rag_query_start", query=query_text, k=k)

        if not self.client.collection_exists(settings.QDRANT_COLLECTION):
            logger.warning(
                "rag_collection_missing",
                collection=settings.QDRANT_COLLECTION,
            )
            return []

        embed_model = self._get_embed_model()
        try:
            index = VectorStoreIndex.from_vector_store(
                self.vector_store,
                storage_context=self.storage_context,
                embed_model=embed_model,
            )

            # 1. Configure retriever for Source Diversity using MMR
            retriever = index.as_retriever(
                similarity_top_k=k * 4,
                vector_store_query_mode="mmr",
                mmr_threshold=0.7,
            )
            nodes = await retriever.aretrieve(query_text)
        except UnexpectedResponse as exc:
            if exc.status_code == 404:
                logger.warning(
                    "rag_collection_unavailable",
                    collection=settings.QDRANT_COLLECTION,
                    error=str(exc),
                )
                return []
            raise

        logger.debug("rag_retrieval_complete", nodes_retrieved=len(nodes))

        # 2. Apply Postprocessor for Unique Files
        postprocessor = UniqueFilePostprocessor()
        filtered_nodes = postprocessor.postprocess_nodes(nodes)

        # 3. Format results (limit to k)
        context = []
        for node in filtered_nodes[:k]:
            context.append(
                {
                    "text": node.node.get_text(),
                    "metadata": node.node.metadata,
                    "score": node.score,
                }
            )

        logger.info("rag_query_complete", nodes_returned=len(context))
        return context


rag_service = RAGService()
