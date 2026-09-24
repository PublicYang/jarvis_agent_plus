"""Tools Layer.

Defines domain tools adhering to LangChain BaseTool and @tool protocols.
"""

from langchain_core.tools import BaseTool

from tools.calculator import calculator
from tools.system import get_system_info

ALL_TOOLS: list[BaseTool] = [
    calculator,
    get_system_info,
]

TOOL_MAP: dict[str, BaseTool] = {tool.name: tool for tool in ALL_TOOLS}

__all__: list[str] = [
    "ALL_TOOLS",
    "TOOL_MAP",
    "calculator",
    "get_system_info",
]
