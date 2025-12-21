from fastapi import APIRouter, HTTPException, Depends
from app.models.schemas import ChatRequest, ChatResponse
from app.services.rag_service import rag_service
from app.services.llm_service import llm_service
from app.core.auth import get_current_user
import uuid
from app.services.history_service import history_service # Added this import as it's used in the new code

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: dict = Depends(get_current_user)):
    try:
        # Default session ID if not provided (transient session)
        session_id = request.session_id or str(uuid.uuid4())
        
        # Determine model
        model_id = request.model_id
        
        # Get history (for context window)
        history = history_service.get_messages(session_id)
        
        # Get Context from RAG
        citations = []
        context = ""
        # Only use RAG if we have documents (check count or just try)
        # We let the service handle lazy loading of the index
        rag_output = await rag_service.query(request.message)
        
        # Build context from ALL chunks
        context = "\n\n".join([c.text for c in rag_output])
        
        # Deduplicate citations for UI (Unique by source filename)
        seen_files = set()
        citations = []
        for c in rag_output:
            if c.source not in seen_files:
                citations.append(c)
                seen_files.add(c.source)
            
        # Generate Response using History + Context
        response_text = ""
        try:
            response_text = await llm_service.generate_response(
                message=request.message,
                context=context,
                history=history,
                model_id=model_id
            )
            # Save to history only on success
            history_service.add_message(session_id, "user", request.message)
            cleaned_response = response_text.replace("assistant: ", "").replace("Assistant: ", "").strip()
            # Convert citations to dicts for storage
            # Pydantic v2 uses model_dump(), v1 used dict()
            citations_dicts = [c.model_dump() for c in citations] if citations else None
            history_service.add_message(session_id, "assistant", cleaned_response, citations=citations_dicts)
            
        except Exception as llm_error:
            import traceback
            traceback.print_exc()
            print(f"LLM Generation Error: {llm_error}", flush=True)
            cleaned_response = "I found some relevant documents, but I'm having trouble generating a response right now. Please check the sources below."

        return ChatResponse(
            response=cleaned_response,
            citations=citations,
            history=history_service.get_messages(session_id),
            session_id=session_id
        )
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Endpoint Error: {e}", flush=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ingest")
async def ingest_documents(current_user: dict = Depends(get_current_user)):
    # Trigger ingestion
    # Logic to point to data/source_documents
    result = await rag_service.ingest_documents("data/source_documents")
    return result
