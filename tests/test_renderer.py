"""Tests for terminal StepRenderer formatting and stream states."""

from io import StringIO
from rich.console import Console

from app.renderer import StepRenderer
from runtime import AgentStep, AgentStepType


def test_step_renderer_tokens_and_transitions(capsys) -> None:
    """Verify StepRenderer handles token streaming and line breaks on state transitions."""
    string_io = StringIO()
    console = Console(file=string_io, color_system=None)
    renderer = StepRenderer(console)

    # 1. Stream tokens
    renderer.render(AgentStep(step_type=AgentStepType.TOKEN, content="Hello"))
    renderer.render(AgentStep(step_type=AgentStepType.TOKEN, content=" world"))
    assert renderer.in_token_stream is True
    assert renderer.has_printed_tokens is True

    # 2. Transition to THOUGHT should close the line with a newline
    renderer.render(AgentStep(step_type=AgentStepType.THOUGHT, content="Need calculation"))
    assert renderer.in_token_stream is False

    # 3. Transition to TOOL_CALL
    renderer.render(
        AgentStep(
            step_type=AgentStepType.TOOL_CALL,
            content="",
            metadata={"name": "calculator", "args": {"expression": "2+2"}},
        )
    )

    # 4. Transition to OBSERVATION
    renderer.render(AgentStep(step_type=AgentStepType.OBSERVATION, content="4"))

    # 5. Transition to FINAL_ANSWER
    renderer.render(AgentStep(step_type=AgentStepType.FINAL_ANSWER, content="Result is 4"))

    # 6. MAX_ITERATIONS warning
    renderer.render(AgentStep(step_type=AgentStepType.MAX_ITERATIONS, content="Loop limit reached"))

    captured = capsys.readouterr()
    stdout_text = captured.out
    rich_text = string_io.getvalue()

    # Verify standard stdout received tokens
    assert "Hello world" in stdout_text
    # Verify console output has thoughts, actions, observations, etc.
    assert "Thinking: Need calculation" in rich_text
    assert "Action: calculator({'expression': '2+2'})" in rich_text
    assert "Observation: 4" in rich_text
    assert "Warning: Loop limit reached" in rich_text
