from typing import List, Optional, Dict, Any
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

    async def _get_llm(self, config: ModelConfig):
        if config.provider == "openai":
            api_key = config.api_key or os.getenv("OPENAI_API_KEY")
            api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            if not api_key:
                raise ValueError("Error: OpenAI API Key not configured.")
            return OpenAI(model=config.id, api_key=api_key, api_base=api_base)

        elif config.provider == "kubeflow":
            # KServe/LocalAI endpoint. We assume standard OpenAI-compatible protocol.
            # We use OpenAILike to bypass strict model name validation in LlamaIndex.
            api_base = config.base_url or os.getenv("LLM_SERVICE_URL")
            # If still None, default to internal DNS
            if not api_base:
                 # Fallback to internal service DNS if not set in env
                 # Note: "llm-service-predictor" is defined in the deployment for KServe
                 api_base = "http://llm-service-predictor.kubeflow-user-example-com.svc.cluster.local:80/v1"
            
            api_key = config.api_key or "dummy" # Internal services usually don't need real keys
            
            from llama_index.llms.openai_like import OpenAILike
            return OpenAILike(
                model=config.id, 
                api_key=api_key, 
                api_base=api_base,
                is_chat_model=True,
                max_tokens=2048
            )

        elif config.provider == "google":
             from llama_index.llms.gemini import Gemini
             api_key = config.api_key or os.getenv("GOOGLE_API_KEY")
             if not api_key:
                 raise ValueError("Error: Google API Key not configured.")
             
             # Gemini maps 'model' kwarg to specific model name, e.g. models/gemini-1.5-flash
             # If config.id already lacks "models/", Gemini class might expect it depending on version.
             # Safe pattern is let the class handle or prepend if needed.
             # The SDK usually expects "models/gemini-1.5-flash-latest" or similar.
             model_name = config.id if config.id.startswith("models/") else f"models/{config.id}"
             return Gemini(model=model_name, api_key=api_key)
        
        elif config.provider == "anthropic":
            raise NotImplementedError("Anthropic provider not yet fully implemented.")
             
        else:
            raise ValueError(f"Provider {config.provider} not supported.")

    async def chat(self, messages: List[Dict[str, str]], model_id: Optional[str] = None) -> str:
        """
        Send a list of messages (dicts) to the LLM and get a response string.
        """
        from llama_index.core.llms import ChatMessage, MessageRole
        
        config = self._get_config(model_id)
        try:
            llm = await self._get_llm(config)
            
            # Convert dicts to ChatMessage
            llama_messages = []
            for msg in messages:
                role_str = msg.get("role", "user")
                content = msg.get("content", "")
                
                role = MessageRole.USER
                if role_str == "system":
                    role = MessageRole.SYSTEM
                elif role_str == "assistant":
                    role = MessageRole.ASSISTANT
                elif role_str == "tool":
                    role = MessageRole.TOOL
                    
                llama_messages.append(ChatMessage(role=role, content=content))
            
            response = await llm.achat(llama_messages)
            return str(response)
            
        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"

    async def generate_response(
        self, 
        message: str, 
        context: str, 
        history: List[Dict[str, str]], 
        model_id: Optional[str] = None
    ) -> str:
        # Prepare system prompt
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

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        # Append history (limited to last 5 pairs to save tokens)
        for msg in history[-5:]:
             role = "user" if msg["role"] == "user" else "assistant"
             messages.append({"role": role, "content": msg["content"]})
        
        messages.append({"role": "user", "content": message})
        
        return await self.chat(messages, model_id)

llm_service = LLMService()
