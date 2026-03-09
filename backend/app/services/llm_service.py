import os
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from langchain_aws import ChatBedrockConverse
from llama_index.llms.openai import OpenAI

# from llama_index.llms.anthropic import Anthropic
from app.models.schemas import ModelConfig
from app.api.endpoints.admin import MODEL_CONFIGS
from app.core.logging import logger
from app.core.config import settings


def build_model_api_path(model_id: str) -> str:
    return model_id.strip().strip("/").replace("/", "-")


def stringify_langchain_content(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [
            item.get("text", "")
            for item in content
            if isinstance(item, dict) and item.get("type") == "text"
        ]
        if text_parts:
            return "\n".join(part for part in text_parts if part)
    return str(content)


@contextmanager
def temporary_bedrock_api_key_env():
    api_key = settings.AWS_BEDROCK_API_KEY.strip()
    if not api_key:
        raise ValueError("Error: AWS_BEDROCK_API_KEY not configured.")

    previous_bearer = os.environ.get("AWS_BEARER_TOKEN_BEDROCK")
    previous_metadata = os.environ.get("AWS_EC2_METADATA_DISABLED")

    os.environ["AWS_BEARER_TOKEN_BEDROCK"] = api_key
    os.environ["AWS_EC2_METADATA_DISABLED"] = "true"

    try:
        yield
    finally:
        if previous_bearer is None:
            os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)
        else:
            os.environ["AWS_BEARER_TOKEN_BEDROCK"] = previous_bearer

        if previous_metadata is None:
            os.environ.pop("AWS_EC2_METADATA_DISABLED", None)
        else:
            os.environ["AWS_EC2_METADATA_DISABLED"] = previous_metadata


class BedrockChatAdapter:
    def __init__(self, chat_model: Any):
        self._chat_model = chat_model

    async def achat(self, messages: List[Any]):
        from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
        from llama_index.core.llms import MessageRole

        langchain_messages = []
        for message in messages:
            content = message.content or ""
            if message.role == MessageRole.SYSTEM:
                langchain_messages.append(SystemMessage(content=content))
            elif message.role == MessageRole.ASSISTANT:
                langchain_messages.append(AIMessage(content=content))
            elif message.role == MessageRole.TOOL:
                langchain_messages.append(ToolMessage(content=content, tool_call_id="tool"))
            else:
                langchain_messages.append(HumanMessage(content=content))

        response = await self._chat_model.ainvoke(langchain_messages)
        return stringify_langchain_content(response.content)


class BedrockLangChainProxy:
    def __init__(self, chat_model: ChatBedrockConverse):
        self._chat_model = chat_model

    async def ainvoke(self, *args: Any, **kwargs: Any) -> Any:
        with temporary_bedrock_api_key_env():
            return await self._chat_model.ainvoke(*args, **kwargs)


class LLMService:
    def __init__(self):
        # We can cache clients if needed
        pass

    def _get_config(self, model_id: Optional[str]) -> ModelConfig:
        if not model_id:
            active = next((m for m in MODEL_CONFIGS if m.is_active), None)
            if active:
                return active

            active_provider = settings.active_provider
            provider_match = next(
                (m for m in MODEL_CONFIGS if m.provider == active_provider), None
            )
            if provider_match:
                return provider_match
            return MODEL_CONFIGS[0]  # Default to first

        config = next((m for m in MODEL_CONFIGS if m.id == model_id), None)
        if not config:
            # Fallback to creating a config on the fly if it's a valid model ID but not in static list
            # This allows flexible model usage
            return ModelConfig(
                id=model_id,
                model_api_path=build_model_api_path(model_id),
                name=model_id,
                provider=settings.active_provider,
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

            model_name = config.id
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"

            return Gemini(model=model_name, api_key=api_key)

        elif config.provider == "aws_bedrock":
            return BedrockChatAdapter(self._create_bedrock_chat_model(config))

        elif config.provider == "anthropic":
            raise NotImplementedError("Anthropic provider not yet fully implemented.")

        else:
            raise ValueError(f"Provider {config.provider} not supported.")

    def get_langchain_model(self, model_id: Optional[str] = None):
        """
        Returns a LangChain BaseChatModel for the specified model ID.
        """
        from langchain_openai import ChatOpenAI

        config = self._get_config(model_id)

        if config.provider == "openai":
            return ChatOpenAI(
                model=config.id,
                api_key=config.api_key or settings.OPENAI_API_KEY,
                temperature=0,
            )

        elif config.provider == "aws_bedrock":
            return self._create_bedrock_chat_model(config)

        elif config.provider == "google":
            # Placeholder for Google via LangChain
            from langchain_google_genai import ChatGoogleGenerativeAI

            return ChatGoogleGenerativeAI(
                model=config.id,
                google_api_key=config.api_key or settings.GOOGLE_API_KEY,
            )

        raise ValueError(f"LangChain provider {config.provider} not supported.")

    def _create_bedrock_chat_model(self, config: ModelConfig) -> BedrockLangChainProxy:
        if not settings.AWS_REGION:
            raise ValueError("Error: AWS_REGION is required for Bedrock SDK clients.")

        with temporary_bedrock_api_key_env():
            chat_model = ChatBedrockConverse(
                model=config.id,
                region_name=settings.AWS_REGION,
                temperature=0,
            )
        return BedrockLangChainProxy(chat_model)

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
