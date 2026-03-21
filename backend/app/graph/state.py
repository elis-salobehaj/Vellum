from typing import List, TypedDict
from langchain_core.messages import BaseMessage
from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    State of the LangGraph RAG workflow.
    """

    messages: List[BaseMessage]  # Chat history
    query: str  # Current search query (can be rewritten)
    documents: List[Document]  # Retrieved documents
    generation: str  # The LLM's answer
    retry_count: int  # Number of retries/rewrites
