"""LLM Adapter Layer.

Provides unified ChatModel factory and multi-provider adapter configurations.
"""

from llm.client import get_chat_model

__all__: list[str] = ["get_chat_model"]
