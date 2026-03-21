from typing import Dict, Any, List
from app.graph.graph import rag_graph


class GraphService:
    """
    Service wrapper for LangGraph execution.
    """

    async def run(
        self, query: str, history: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute the RAG graph for a given query.
        """
        initial_state = {
            "query": query,
            "messages": [],  # Could populate from history
            "documents": [],
            "generation": "",
            "retry_count": 0,
        }

        # Invoke the graph
        # config={"recursion_limit": 50}
        result = await rag_graph.ainvoke(initial_state)

        # Format response
        return {
            "response": result["generation"],
            "citations": [
                {
                    "source": doc.metadata.get("file_name", "unknown"),
                    "page": doc.metadata.get("page_label", 1),
                    "text": doc.page_content,
                    "score": doc.metadata.get("score"),
                }
                for doc in result.get("documents", [])
            ],
        }


graph_service = GraphService()
