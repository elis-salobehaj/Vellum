from typing import Literal

from langgraph.graph import StateGraph, END
from app.graph.state import GraphState
from app.graph.nodes import GraphNodes
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service


class GraphBuilder:
    def __init__(self, llm_service, rag_service):
        self.llm_service = llm_service
        self.rag_service = rag_service
        self.nodes = GraphNodes(llm_service, rag_service)

    def decide_to_generate(
        self, state: GraphState
    ) -> Literal["generate", "transform_query"]:
        """
        Determines whether to generate an answer, or re-generate a question.
        """
        print("---DECIDE TO GENERATE---")

        if not state.get("documents"):
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            # print("---DECISION: TRANSFORM QUERY---")
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            # print("---DECISION: GENERATE---")
            return "generate"

    def build(self):
        workflow = StateGraph(GraphState)

        # Define the nodes
        workflow.add_node("retrieve", self.nodes.retrieve)
        workflow.add_node("grade_documents", self.nodes.grade_documents)
        workflow.add_node("generate", self.nodes.generate)
        workflow.add_node("transform_query", self.nodes.transform_query)

        # Build graph
        workflow.set_entry_point("retrieve")

        workflow.add_edge("retrieve", "grade_documents")

        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "transform_query": "transform_query",
                "generate": "generate",
            },
        )

        workflow.add_edge("transform_query", "retrieve")
        workflow.add_edge("generate", END)

        # Compile
        return workflow.compile()


def create_graph(llm_service, rag_service):
    builder = GraphBuilder(llm_service, rag_service)
    return builder.build()


# Default instance for backward compatibility
rag_graph = create_graph(llm_service, rag_service)
