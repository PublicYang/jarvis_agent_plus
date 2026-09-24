"""System environment query tool definition."""

import platform

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class SystemInfoInput(BaseModel):
    """Input schema for system information tool."""

    query_type: str = Field(
        default="all",
        description="Type of system information requested: 'os', 'python', or 'all'",
    )


@tool("get_system_info", args_schema=SystemInfoInput)
def get_system_info(query_type: str = "all") -> str:
    """Query current host system and runtime environment information."""
    os_name = platform.system()
    release = platform.release()
    py_version = platform.python_version()

    match query_type.lower():
        case "os":
            return f"OS: {os_name} {release}"
        case "python":
            return f"Python Version: {py_version}"
        case _:
            return f"Operating System: {os_name} {release} | Python: {py_version}"
