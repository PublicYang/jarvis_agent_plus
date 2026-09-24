"""Tests for prompt templates, output parsers, and end-to-end chains."""

import pytest
from langchain_core.exceptions import OutputParserException
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from prompts import (
    create_chat_prompt,
    create_instruction_prompt,
    create_pydantic_parser,
    extract_format_instructions,
    get_json_parser,
    get_string_parser,
)
from runtime import compose_sequence, make_lambda


class TaskPlan(BaseModel):
    """Pydantic model representing structured plan output."""

    task_name: str = Field(description="Name of the task")
    priority: int = Field(description="Priority score from 1 to 5")


def test_chat_prompt_rendering() -> None:
    """Verify ChatPromptTemplate renders system and human messages correctly."""
    prompt = create_chat_prompt(
        system_prompt="You are a helpful assistant.",
        input_key="user_query",
    )
    formatted = prompt.invoke({"user_query": "What is Python?"})
    messages = formatted.to_messages()

    assert len(messages) == 2
    assert isinstance(messages[0], SystemMessage)
    assert messages[0].content == "You are a helpful assistant."
    assert isinstance(messages[1], HumanMessage)
    assert messages[1].content == "What is Python?"


def test_chat_prompt_with_history() -> None:
    """Verify history placeholder embeds prior dialogue messages seamlessly."""
    prompt = create_chat_prompt(
        system_prompt="You remember things.",
        history_key="history",
        input_key="input",
    )
    history_messages = [
        HumanMessage(content="My name is Bob"),
        AIMessage(content="Nice to meet you Bob"),
    ]
    formatted = prompt.invoke(
        {"input": "What is my name?", "history": history_messages}
    )
    messages = formatted.to_messages()

    assert len(messages) == 4
    assert messages[0].content == "You remember things."
    assert messages[1].content == "My name is Bob"
    assert messages[2].content == "Nice to meet you Bob"
    assert messages[3].content == "What is my name?"


def test_chat_prompt_partial_variables() -> None:
    """Verify partial formatting pre-binds global variables."""
    prompt = create_chat_prompt(
        system_prompt="Platform: {platform}. Target: {target}.",
        partial_vars={"platform": "Linux"},
    )
    formatted = prompt.invoke({"target": "AgentPlus", "input": "Hello"})
    messages = formatted.to_messages()

    assert "Platform: Linux. Target: AgentPlus." in messages[0].content


def test_str_output_parser_end_to_end() -> None:
    """Verify end-to-end chain with StrOutputParser: Prompt -> LLM -> Parser."""
    prompt = create_chat_prompt(system_prompt="You echo responses.")
    fake_llm = make_lambda(lambda _: AIMessage(content="Echo: Hello!"))
    parser = get_string_parser()

    chain = compose_sequence(prompt, fake_llm, parser)
    result = chain.invoke({"input": "Hello!"})

    assert result == "Echo: Hello!"


def test_pydantic_output_parser_end_to_end() -> None:
    """Verify end-to-end structured chain: Prompt -> LLM -> PydanticOutputParser."""
    parser = create_pydantic_parser(TaskPlan)
    instructions = extract_format_instructions(parser)

    prompt = create_instruction_prompt(
        system_prompt="Generate plan adhering to instructions.",
        format_instructions=instructions,
    )
    raw_json_response = '{"task_name": "Release V1", "priority": 5}'
    fake_llm = make_lambda(lambda _: AIMessage(content=raw_json_response))

    chain = compose_sequence(prompt, fake_llm, parser)
    result = chain.invoke({"input": "Plan next release"})

    assert isinstance(result, TaskPlan)
    assert result.task_name == "Release V1"
    assert result.priority == 5


def test_pydantic_output_parser_validation_error() -> None:
    """Verify PydanticOutputParser raises OutputParserException on schema mismatch."""
    parser = create_pydantic_parser(TaskPlan)
    fake_llm = make_lambda(lambda _: AIMessage(content="Invalid non-JSON response"))

    chain = compose_sequence(
        create_chat_prompt(system_prompt="Assistant"),
        fake_llm,
        parser,
    )

    with pytest.raises(OutputParserException):
        chain.invoke({"input": "test"})


def test_json_output_parser_end_to_end() -> None:
    """Verify JsonOutputParser extracts dict structures."""
    fake_llm = make_lambda(
        lambda _: AIMessage(content='{"status": "success", "code": 200}')
    )
    chain = compose_sequence(
        create_chat_prompt(system_prompt="JSON API"),
        fake_llm,
        get_json_parser(),
    )
    result = chain.invoke({"input": "query"})
    assert result == {"status": "success", "code": 200}
