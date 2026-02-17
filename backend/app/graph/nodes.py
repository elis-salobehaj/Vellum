from typing import Any, Dict
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.documents import Document
from app.graph.state import GraphState
from app.core.logging import logger


class GraphNodes:
    """
    Nodes for the LangGraph RAG workflow.
    """

    def __init__(self, llm_service, rag_service):
        self.llm_service = llm_service
        self.rag_service = rag_service

    async def retrieve(self, state: GraphState) -> Dict[str, Any]:
        """
        Retrieve documents from vector store.
        """

        logger.info("---RETRIEVE---")
        query = state["query"]

        # Use injected RAG service
        # We might want to increase 'k' for the graph to have more candidates to grade
        results = await self.rag_service.query(query, k=5)

        documents = []
        for res in results:
            doc = Document(page_content=res["text"], metadata=res["metadata"] or {})
            # Add score to metadata if needed
            if res.get("score"):
                doc.metadata["score"] = res["score"]
            documents.append(doc)

        return {"documents": documents, "query": query}

    async def grade_documents(self, state: GraphState) -> Dict[str, Any]:
        """
        Determines whether the retrieved documents are relevant to the question.
        """

        logger.info("---CHECK RELEVANCE---")
        query = state["query"]

        documents = state["documents"]

        # LLM for grading - use a fast model
        # We'll use the default active model for now, but in prod use "gpt-4o-mini"
        llm = self.llm_service.get_langchain_model()

        filtered_docs = []

        system_prompt = """You are a grader assessing relevance of a retrieved document to a user question. \n 
        If the document contains keyword(s) or semantic meaning related to the question, grade it as relevant. \n
        Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question."""

        for doc in documents:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(
                    content=f"Retrieved document: \n\n {doc.page_content} \n\n User question: {query}"
                ),
            ]

            # Simple invocation
            response = await llm.ainvoke(messages)
            grade = response.content.lower().strip()

            if "yes" in grade:
                logger.info("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(doc)
            else:
                logger.info("---GRADE: DOCUMENT NOT RELEVANT---")
                continue

        return {"documents": filtered_docs}

    async def generate(self, state: GraphState) -> Dict[str, Any]:
        """
        Generate answer.
        """

        logger.info("---GENERATE---")
        query = state["query"]

        documents = state["documents"]

        llm = self.llm_service.get_langchain_model()

        # Determine context
        context = "\n\n".join([doc.page_content for doc in documents])

        system_prompt = """You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Question: {query} \n\n Context: {context}"),
        ]

        response = await llm.ainvoke(messages)
        return {"generation": response.content}

    async def transform_query(self, state: GraphState) -> Dict[str, Any]:
        """
        Transform the query to produce a better question.
        """

        logger.info("---TRANSFORM QUERY---")
        query = state["query"]

        llm = self.llm_service.get_langchain_model()

        system_prompt = """You are a helpful assistant that generates multiple search queries based on a single input query. \n
        Generate a single better search query that is more likely to retrieve relevant information."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Input: {query}"),
        ]

        response = await llm.ainvoke(messages)
        better_query = response.content.strip()

        return {"query": better_query}
