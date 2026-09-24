"""Tool execution dispatcher and model binding adapter."""

from collections.abc import Sequence
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool


def bind_model_tools(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
) -> Runnable[Any, AIMessage]:
    """Bind a sequence of standard BaseTools to a ChatModel."""
    return model.bind_tools(list(tools))


def has_tool_calls(message: AIMessage) -> bool:
    """Check if the given AIMessage requests any tool execution."""
    return bool(getattr(message, "tool_calls", None))


def execute_tool_calls(
    tool_calls: list[dict[str, Any]],
    tool_map: dict[str, BaseTool],
) -> list[ToolMessage]:
    """Execute a list of tool calls and wrap their results into ToolMessages."""
    results: list[ToolMessage] = []

    for call in tool_calls:
        tool_name = call.get("name", "")
        tool_args = call.get("args", {})
        call_id = call.get("id", "missing_tool_call_id")

        tool = tool_map.get(tool_name)
        if not tool:
            error_msg = f"Tool '{tool_name}' not found in registry."
            results.append(
                ToolMessage(
                    content=error_msg,
                    tool_call_id=call_id,
                    name=tool_name,
                    status="error",
                )
            )
            continue

        try:
            tool_output = tool.invoke(tool_args)
            results.append(
                ToolMessage(
                    content=str(tool_output),
                    tool_call_id=call_id,
                    name=tool_name,
                    status="success",
                )
            )
        except Exception as exc:
            results.append(
                ToolMessage(
                    content=f"Tool '{tool_name}' failed with error: {exc}",
                    tool_call_id=call_id,
                    name=tool_name,
                    status="error",
                )
            )

    return results
