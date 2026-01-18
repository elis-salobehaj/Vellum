from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Dict, Any
from app.services.llm_service import llm_service
from app.services.rag_service import rag_service
from app.core.auth import get_current_user
from app.core.config import settings
from minio import Minio

router = APIRouter()

from typing import List, Dict, Any, Optional
# Removed uuid import as generation is now handled by frontend or history service

from app.models.schemas import ChatRequest, ChatResponse, Citation

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    """
    Chat endpoint.
    1. Retrieve relevant context from Qdrant via RAG Service.
    2. Augment prompt.
    3. Generate response via LLM Service.
    """
    # 0. Handle Session ID (pass-through from request)
    session_id = request.session_id

    # 1. Retrieve Context
    context_nodes = await rag_service.query(request.message, k=request.context_window)
    
    # Map context nodes to Citations
    citations = []
    for node in context_nodes:
        metadata = node.get("metadata", {})
        citations.append(Citation(
            text=node["text"],
            source=metadata.get("file_name", "unknown"),
            page=int(metadata.get("page_label", 0)) if metadata.get("page_label") else 0,
            score=node.get("score")
        ))
    
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
        {"role": "user", "content": request.message}
    ]

    # 3. Generate Response
    # Note: We currently ignore request.model_id as the backend is configured centrally or via env.
    # Future work: Pass model_id to llm_service if dynamic switching is needed.
    response_text = await llm_service.chat(messages)
    
    return ChatResponse(
        response=response_text, 
        citations=citations, 
        session_id=session_id
    )

@router.get("/files/{filename:path}")
async def get_file_proxy(filename: str):
    """
    Proxy request to MinIO to serve the file directly.
    """
    try:
        # Initialize MinIO client locally for the proxy
        # We use the internal kubeflow svc endpoint
        client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=False
        )
        
        # Get object from MinIO
        response = client.get_object(settings.MINIO_BUCKET, filename)
        
        # Stream the response back to the user
        return StreamingResponse(
            response.stream(32*1024),
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"File not found: {str(e)}")
