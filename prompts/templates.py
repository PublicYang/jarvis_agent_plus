"""Structured ChatPromptTemplate factories and prompt utilities."""

from typing import Any

from langchain_core.prompts import (
    BaseChatPromptTemplate,
    ChatPromptTemplate,
    MessagesPlaceholder,
)


def create_chat_prompt(
    system_prompt: str,
    input_key: str = "input",
    history_key: str | None = "chat_history",
    partial_vars: dict[str, Any] | None = None,
) -> BaseChatPromptTemplate:
    """Create a structured ChatPromptTemplate.

    Supports system instruction, optional history placeholder, and user input.

    Args:
        system_prompt: Base system instruction or persona.
        input_key: Variable name for the user's latest query.
        history_key: Variable name for prior conversation messages.
        partial_vars: Pre-filled variables (e.g. current_time, platform).
    """
    messages: list[Any] = [("system", system_prompt)]

    if history_key:
        messages.append(MessagesPlaceholder(variable_name=history_key, optional=True))

    messages.append(("human", f"{{{input_key}}}"))

    prompt = ChatPromptTemplate.from_messages(messages)
    if partial_vars:
        prompt = prompt.partial(**partial_vars)

    return prompt


def create_instruction_prompt(
    system_prompt: str,
    format_instructions: str,
    input_key: str = "input",
) -> BaseChatPromptTemplate:
    """Create a prompt that incorporates output schema formatting instructions."""
    # Escape curly braces in schema instructions to avoid f-string syntax errors
    escaped_instructions = format_instructions.replace("{", "{{").replace("}", "}}")
    combined_system = (
        f"{system_prompt}\n\n[OUTPUT INSTRUCTIONS]\n{escaped_instructions}"
    )
    return ChatPromptTemplate.from_messages(
        [
            ("system", combined_system),
            ("human", f"{{{input_key}}}"),
        ]
    )
