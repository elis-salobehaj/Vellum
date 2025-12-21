from typing import List, Optional, Dict, Any
import torch
import os
from llama_index.llms.openai import OpenAI
# from llama_index.llms.anthropic import Anthropic
from app.models.schemas import ModelConfig
from app.api.endpoints.admin import MODEL_CONFIGS

class LLMService:
    def __init__(self):
        # We can cache clients if needed
        pass

    def _get_config(self, model_id: Optional[str]) -> ModelConfig:
        if not model_id:
            # Find active
            active = next((m for m in MODEL_CONFIGS if m.is_active), None)
            if active: 
                return active
            return MODEL_CONFIGS[0] # Default to first
        
        config = next((m for m in MODEL_CONFIGS if m.id == model_id), None)
        if not config:
             raise ValueError(f"Model ID {model_id} not found")
        return config

    async def generate_response(
        self, 
        message: str, 
        context: str, 
        history: List[Dict[str, str]], 
        model_id: Optional[str] = None
    ) -> str:
        config = self._get_config(model_id)
        
        # Prepare system        # Prepare messages
        system_prompt = (
            "You are an expert AI assistant specializing in Artificial Intelligence, Agentic AI, and Large Language Models (LLMs). "
            "Your goal is to provide technical, accurate, and concise insights based on the provided context.\n"
            "INSTRUCTIONS:\n"
            "1. Analyze the Context provided below carefully.\n"
            "2. If the Context contains the answer, strictly base your response on it and cite the source using the format [Source: Filename].\n"
            "3. If the Context is empty, you MUST explicitely state 'no context found' at the beginning of your response.\n"
            "4. After stating 'no context found', you may proceed to answer using your expert knowledge.\n"
            "5. Maintain a professional, knowledgeable tone.\n\n"
            f"Context:\n{context}\n"
        )

        from llama_index.core.llms import ChatMessage, MessageRole

        messages = [
            ChatMessage(role=MessageRole.SYSTEM, content=system_prompt),
        ]
        # Append history (limited to last 5 pairs to save tokens)
        for msg in history[-10:]:
             role = MessageRole.USER if msg["role"] == "user" else MessageRole.ASSISTANT
             messages.append(ChatMessage(role=role, content=msg["content"]))
        
        messages.append(ChatMessage(role=MessageRole.USER, content=message))

        try:
            if config.provider == "openai":
                # Ensure API key is set
                api_key = config.api_key or os.getenv("OPENAI_API_KEY")
                if not api_key:
                    return "Error: OpenAI API Key not configured."
                
                llm = OpenAI(model=config.id, api_key=api_key)
                response = await llm.achat(messages) # LlamaIndex chat
                return str(response)

            elif config.provider == "google":
                from llama_index.llms.gemini import Gemini
                api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
                if not api_key:
                    return "Error: Google API Key not configured."
                
                # Gemini maps 'model' kwarg to the specific model name e.g. models/gemini-pro
                llm = Gemini(model=f"models/{config.id}", api_key=api_key)
                response = await llm.achat(messages)
                return str(response)
            
            elif config.provider == "anthropic":
                # Placeholder for Anthropic
                return "Anthropic provider not yet fully implemented."
                
            elif config.provider == "local" or config.provider == "ollama":
                 from llama_index.llms.ollama import Ollama
                 
                 # Using Ollama (requires Ollama running on host or container)
                 # base_url is from env or default
                 llm = Ollama(
                    model=config.id, 
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434"),
                    request_timeout=300.0
                 )
                 
                 response = await llm.achat(messages)
                 return str(response)
            
            else:
                return f"Provider {config.provider} not supported."

        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"

llm_service = LLMService()
