"""LLM Client and ChatModel factory adapter."""

import os
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI


def get_chat_model(
    model_name: str | None = None,
    temperature: float = 0.0,
    api_key: str | None = None,
    base_url: str | None = None,
    streaming: bool = False,
    **kwargs: Any,
) -> BaseChatModel:
    """Create and return a configured BaseChatModel instance.

    Reads defaults from environment variables:
    - OPENAI_MODEL_NAME (default: "gpt-4o-mini")
    - OPENAI_API_KEY (default: "dummy-key-for-local-dev" if unset)
    - OPENAI_BASE_URL (optional)
    """
    resolved_model = model_name or os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    resolved_key = api_key or os.getenv("OPENAI_API_KEY") or "dummy-key-for-local-dev"
    resolved_base_url = base_url or os.getenv("OPENAI_BASE_URL")

    client_kwargs: dict[str, Any] = {
        "model": resolved_model,
        "temperature": temperature,
        "api_key": resolved_key,
        "streaming": streaming,
        **kwargs,
    }
    if resolved_base_url:
        client_kwargs["base_url"] = resolved_base_url

    return ChatOpenAI(**client_kwargs)
