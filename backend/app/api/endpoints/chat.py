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

    # 1. Retrieve Context
    context_nodes = await rag_service.query(request.message, k=request.context_window)

    # Map context nodes to Citations
    citations = []
    for node in context_nodes:
        metadata = node.get("metadata", {})
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
    system_prompt = (
        "You are an AI assistant for Vellum. "
        "Use the following context to answer the user's question. "
        "If the answer is not in the context, say you don't know. "
        "Answer directly.\n\n"
        f"Context:\n{context_text}"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": request.message},
    ]

    # 3. Generate Response
    response_text = await llm_service.chat(messages)

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
