from typing import List, Optional, Dict
from llama_index.llms.openai import OpenAI

# from llama_index.llms.anthropic import Anthropic
from app.models.schemas import ModelConfig
from app.api.endpoints.admin import MODEL_CONFIGS
from app.core.logging import logger
from app.core.config import settings


class LLMService:
    def __init__(self):
        # We can cache clients if needed
        pass

    def _get_config(self, model_id: Optional[str]) -> ModelConfig:
        if not model_id:
            # Find active based on settings.active_provider
            active_provider = settings.active_provider
            # Try to find a config matching the active provider
            active = next(
                (m for m in MODEL_CONFIGS if m.provider == active_provider), None
            )
            if active:
                return active

            # Fallback to any active model
            active = next((m for m in MODEL_CONFIGS if m.is_active), None)
            if active:
                return active
            return MODEL_CONFIGS[0]  # Default to first

        config = next((m for m in MODEL_CONFIGS if m.id == model_id), None)
        if not config:
            # Fallback to creating a config on the fly if it's a valid model ID but not in static list
            # This allows flexible model usage
            return ModelConfig(
                id=model_id, name=model_id, provider=settings.active_provider
            )
        return config

    async def _get_llm(self, config: ModelConfig):
        if config.provider == "openai":
            api_key = config.api_key or settings.OPENAI_API_KEY
            api_base = settings.OPENAI_API_BASE
            if not api_key:
                raise ValueError("Error: OpenAI API Key not configured.")
            return OpenAI(model=config.id, api_key=api_key, api_base=api_base)

        elif config.provider == "kubeflow":
            # KServe/LocalAI endpoint. We assume standard OpenAI-compatible protocol.
            # We use OpenAILike to bypass strict model name validation in LlamaIndex.
            api_base = config.base_url or settings.LLM_SERVICE_URL
            # If still None, default to internal DNS
            if not api_base:
                api_base = settings.LLM_SERVICE_URL

            api_key = (
                config.api_key or "dummy"
            )  # Internal services usually don't need real keys

            from llama_index.llms.openai_like import OpenAILike

            return OpenAILike(
                model=config.id,
                api_key=api_key,
                api_base=api_base,
                is_chat_model=True,
                max_tokens=2048,
            )

        elif config.provider == "google":
            from llama_index.llms.gemini import Gemini

            api_key = config.api_key or settings.GOOGLE_API_KEY
            if not api_key:
                raise ValueError("Error: Google API Key not configured.")

            # Use the model name as provided in config
            return Gemini(model=config.id, api_key=api_key)

        elif config.provider == "aws_bedrock":
            from llama_index.llms.bedrock import Bedrock

            return Bedrock(
                model=config.id,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=config.region or settings.AWS_REGION,
                context_size=8192,  # Default for Claude models generally
            )

        elif config.provider == "anthropic":
            raise NotImplementedError("Anthropic provider not yet fully implemented.")

        else:
            raise ValueError(f"Provider {config.provider} not supported.")

    def get_langchain_model(self, model_id: Optional[str] = None):
        """
        Returns a LangChain BaseChatModel for the specified model ID.
        """
        from langchain_openai import ChatOpenAI
        from langchain_aws import ChatBedrock
        from app.core.config import settings

        config = self._get_config(model_id)

        if config.provider == "openai":
            return ChatOpenAI(
                model=config.id,
                api_key=config.api_key or settings.OPENAI_API_KEY,
                temperature=0,
            )

        elif config.provider == "aws_bedrock":
            # Bedrock specific config
            import boto3

            bedrock_client = boto3.client(
                service_name="bedrock-runtime",
                region_name=config.region or settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            return ChatBedrock(
                model_id=config.id,
                client=bedrock_client,
                model_kwargs={"temperature": 0},
            )

        elif config.provider == "google":
            # Placeholder for Google via LangChain
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=config.id,
                google_api_key=config.api_key or settings.GOOGLE_API_KEY,
            )

        raise ValueError(f"LangChain provider {config.provider} not supported.")

    async def chat(
        self, messages: List[Dict[str, str]], model_id: Optional[str] = None
    ) -> str:
        """
        Send a list of messages (dicts) to the LLM and get a response string.
        """
        from llama_index.core.llms import ChatMessage, MessageRole

        config = self._get_config(model_id)
        try:
            logger.info("llm_request_start", model=config.id, provider=config.provider)
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
            logger.info("llm_request_complete", model=config.id)
            return str(response)

        except Exception as e:
            logger.error("llm_request_failed", error=str(e), model=config.id)
            return f"Error communicating with LLM: {str(e)}"

    async def generate_response(
        self,
        message: str,
        context: str,
        history: List[Dict[str, str]],
        model_id: Optional[str] = None,
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
