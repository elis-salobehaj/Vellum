from fastapi import APIRouter, Depends
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.services.history_service import history_service
from app.core.auth import get_current_user
from app.models.schemas import ChatRequest, ChatResponse, Citation
import uuid

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Chat endpoint.
    1. Retrieve relevant context from Qdrant via RAG Service.
    2. Augment prompt.
    3. Generate response via LLM Service.
    """
    # 0. Handle Session ID
    session_id = request.session_id or str(uuid.uuid4())

    # Save User Message to History
    history_service.add_message(session_id, "user", request.message)

    # 1. Retrieve Context / OR Run Graph
    response_text = ""
    citations = []

    if request.use_graph:
        from app.services.graph_service import graph_service

        # Graph execution (LangGraph)
        result = await graph_service.run(request.message)
        response_text = result["response"]

        for c in result["citations"]:
            citations.append(
                Citation(
                    text=c["text"], source=c["source"], page=c["page"], score=c["score"]
                )
            )

    else:
        # Standard Linear RAG
        context_nodes = await rag_service.query(
            request.message, k=request.context_window
        )

        # Map context nodes to Citations
        citations = []
        for node in context_nodes:
            metadata = node.get("metadata", {}) or {}  # Handle None metadata
            citations.append(
                Citation(
                    text=node["text"],
                    source=metadata.get("file_name", "unknown"),
                    page=int(metadata.get("page_label", 0))
                    if metadata.get("page_label")
                    else 0,
                    score=node.get("score"),
                )
            )

        # 2. Augment Prompt
        context_text = "\n\n".join([c.text for c in citations])

        # Use simple system prompt for now
        messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Use the provided context to answer the question.",
            },
            {
                "role": "user",
                "content": f"Context:\n{context_text}\n\nQuestion: {request.message}",
            },
        ]

        # 3. Generate Response
        response_text = await llm_service.chat(messages, model_id=request.model_id)

    # 4. Save Assistant Response to History
    history_service.add_message(
        session_id,
        "assistant",
        response_text,
        citations=[c.model_dump() for c in citations],
    )

    return ChatResponse(
        response=response_text, citations=citations, session_id=session_id
    )
