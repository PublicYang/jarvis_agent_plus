"""Stateful chain wrapper and session-aware LCEL execution."""

from collections.abc import Callable, Iterator
from typing import Any

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables import Runnable
from langchain_core.runnables.history import RunnableWithMessageHistory


def create_stateful_chain(
    runnable: Runnable,
    get_session_history: Callable[[str], BaseChatMessageHistory],
    input_messages_key: str = "input",
    history_messages_key: str = "chat_history",
    output_messages_key: str | None = None,
) -> RunnableWithMessageHistory:
    """Wrap an LCEL chain with session-based chat message history.

    Args:
        runnable: Underlying stateless LCEL Runnable (e.g. Prompt | LLM | Parser).
        get_session_history: Callable taking session_id (str) and returning history.
        input_messages_key: Key in the input dict containing the user message.
        history_messages_key: Key matching the MessagesPlaceholder in prompt template.
        output_messages_key: Key in output dict if runnable returns a dict.

    Returns:
        A RunnableWithMessageHistory instance that accepts session_id in config:
        `config={"configurable": {"session_id": "session_id"}}`
    """
    return RunnableWithMessageHistory(
        runnable=runnable,
        get_session_history=get_session_history,
        input_messages_key=input_messages_key,
        history_messages_key=history_messages_key,
        output_messages_key=output_messages_key,
    )


def invoke_with_session(
    chain: RunnableWithMessageHistory,
    input_text: str,
    session_id: str = "default",
    input_key: str = "input",
    **extra_inputs: Any,
) -> Any:
    """Invoke a stateful chain for a given session_id.

    Args:
        chain: The RunnableWithMessageHistory wrapped chain.
        input_text: User message text.
        session_id: Session identifier for context isolation.
        input_key: Key corresponding to input_messages_key.
        **extra_inputs: Additional prompt variables to pass.

    Returns:
        The output produced by the chain.
    """
    payload = {input_key: input_text, **extra_inputs}
    config = {"configurable": {"session_id": session_id}}
    return chain.invoke(payload, config=config)


def stream_with_session(
    chain: RunnableWithMessageHistory,
    input_text: str,
    session_id: str = "default",
    input_key: str = "input",
    **extra_inputs: Any,
) -> Iterator[Any]:
    """Stream token/chunks from a stateful chain for a given session_id.

    Args:
        chain: The RunnableWithMessageHistory wrapped chain.
        input_text: User message text.
        session_id: Session identifier for context isolation.
        input_key: Key corresponding to input_messages_key.
        **extra_inputs: Additional prompt variables to pass.

    Yields:
        Chunks produced by the underlying chain.
    """
    payload = {input_key: input_text, **extra_inputs}
    config = {"configurable": {"session_id": session_id}}
    yield from chain.stream(payload, config=config)
