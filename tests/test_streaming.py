"""Tests for streaming runtime generators and CLI commands."""

from collections.abc import Iterator

import pytest
from typer.testing import CliRunner

from app.cli import app
from runtime import (
    astream_pipeline_events,
    compose_sequence,
    make_lambda,
    stream_text,
)

runner = CliRunner()


def test_stream_text_chunks() -> None:
    """Verify stream_text yields tokens sequentially from a generator chain."""

    def mock_stream(data: dict[str, str]) -> Iterator[str]:
        tokens = ["Streaming", " ", "LCEL", " ", "Tokens"]
        yield from tokens

    chain = compose_sequence(make_lambda(mock_stream))
    chunks = list(stream_text(chain, {"input": "test"}))

    assert chunks == ["Streaming", " ", "LCEL", " ", "Tokens"]
    assert "".join(chunks) == "Streaming LCEL Tokens"


@pytest.mark.asyncio
async def test_astream_pipeline_events() -> None:
    """Verify astream_pipeline_events yields structured lifecycle events."""
    chain = compose_sequence(make_lambda(lambda x: x["value"].upper()))

    events = []
    async for event in astream_pipeline_events(chain, {"value": "hello"}):
        events.append(event["event"])

    assert "on_chain_start" in events
    assert "on_chain_end" in events


def test_cli_tools_command() -> None:
    """Verify 'jarvis tools' CLI command renders the registered tools table."""
    result = runner.invoke(app, ["tools"])
    assert result.exit_code == 0
    assert "calculator" in result.stdout
    assert "get_system_info" in result.stdout


def test_cli_ask_command_graceful_handling() -> None:
    """Verify 'jarvis ask' CLI command executes and outputs content or tips."""
    result = runner.invoke(app, ["ask", "Hello Jarvis", "--model", "gpt-4o-mini"])
    assert result.exit_code == 0
    assert "Jarvis Agent Plus" in result.stdout
    assert "Hello Jarvis" in result.stdout
