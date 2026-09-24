"""Tests for tool schemas, model tool binding, and execution dispatching."""

from langchain_core.messages import AIMessage, ToolMessage

from llm import get_chat_model
from runtime import (
    bind_model_tools,
    execute_tool_calls,
    has_tool_calls,
)
from tools import ALL_TOOLS, TOOL_MAP, calculator, get_system_info


def test_calculator_tool_execution() -> None:
    """Verify calculator tool performs arithmetic safely."""
    assert calculator.invoke({"expression": "2 + 3 * 4"}) == "14"
    assert calculator.invoke({"expression": "2 ** 5"}) == "32"
    assert calculator.invoke({"expression": "100 / 4"}) == "25.0"

    # Test syntax error handling without crashing
    error_result = calculator.invoke({"expression": "__import__('os')"})
    assert "Error evaluating expression" in error_result


def test_system_info_tool_execution() -> None:
    """Verify system info tool retrieves valid host metrics."""
    os_info = get_system_info.invoke({"query_type": "os"})
    assert "OS:" in os_info

    py_info = get_system_info.invoke({"query_type": "python"})
    assert "Python Version:" in py_info


def test_tool_schema_extraction() -> None:
    """Verify tool schemas are extracted automatically from Pydantic models."""
    schema = calculator.args_schema.model_json_schema()
    assert "expression" in schema["properties"]
    assert "description" in schema["properties"]["expression"]


def test_bind_model_tools_interface() -> None:
    """Verify ChatModel binds tools and generates a Runnable sequence."""
    model = get_chat_model(model_name="gpt-4o-mini")
    bound_model = bind_model_tools(model, ALL_TOOLS)
    assert hasattr(bound_model, "invoke")


def test_has_tool_calls_helper() -> None:
    """Verify detection of tool calls in AIMessage."""
    msg_without_tools = AIMessage(content="Just chatting.")
    assert not has_tool_calls(msg_without_tools)

    msg_with_tools = AIMessage(
        content="",
        tool_calls=[{"name": "calculator", "args": {"expression": "1+1"}, "id": "1"}],
    )
    assert has_tool_calls(msg_with_tools)


def test_execute_tool_calls_dispatch() -> None:
    """Verify tool execution dispatcher dispatches and packages ToolMessages."""
    simulated_calls = [
        {
            "name": "calculator",
            "args": {"expression": "7 * 8"},
            "id": "call_calc_01",
        },
        {
            "name": "get_system_info",
            "args": {"query_type": "os"},
            "id": "call_sys_02",
        },
    ]

    messages = execute_tool_calls(simulated_calls, TOOL_MAP)
    assert len(messages) == 2

    assert isinstance(messages[0], ToolMessage)
    assert messages[0].tool_call_id == "call_calc_01"
    assert messages[0].content == "56"
    assert messages[0].status == "success"

    assert isinstance(messages[1], ToolMessage)
    assert messages[1].tool_call_id == "call_sys_02"
    assert "OS:" in messages[1].content
    assert messages[1].status == "success"


def test_execute_tool_calls_unknown_tool() -> None:
    """Verify dispatcher gracefully captures missing tools as error ToolMessages."""
    simulated_calls = [
        {
            "name": "unknown_tool",
            "args": {},
            "id": "call_missing_99",
        }
    ]

    messages = execute_tool_calls(simulated_calls, TOOL_MAP)
    assert len(messages) == 1
    assert messages[0].tool_call_id == "call_missing_99"
    assert messages[0].status == "error"
    assert "not found in registry" in messages[0].content
