"""Streaming response generators and event dispatchers."""

from collections.abc import AsyncIterator, Iterator
from typing import Any

from langchain_core.runnables import Runnable


def stream_text(chain: Runnable[Any, Any], input_data: Any) -> Iterator[str]:
    """Yield text chunks synchronously from an LCEL chain."""
    for chunk in chain.stream(input_data):
        if isinstance(chunk, str):
            yield chunk
        elif hasattr(chunk, "content") and isinstance(chunk.content, str):
            yield chunk.content
        else:
            yield str(chunk)


async def astream_pipeline_events(
    chain: Runnable[Any, Any],
    input_data: Any,
) -> AsyncIterator[dict[str, Any]]:
    """Yield structured execution events from an LCEL chain via astream_events v2."""
    async for event in chain.astream_events(input_data, version="v2"):
        yield event
