"""Tests for MiniAgent ReAct execution loop, tool dispatch, and memory bridging."""

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from memory import FileHistoryStore
from runtime import AgentStepType, MiniAgent
from tools import calculator, get_system_info


class ScriptedChatModel(BaseChatModel):
    """A mock chat model that plays back a predetermined sequence of AIMessages."""

    scripted_responses: Sequence[AIMessage] = []
    current_index: int = 0
    received_message_history: list[list[BaseMessage]] = []

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: Any = None,
        **kwargs: Any,
    ) -> ChatResult:
        self.received_message_history.append(list(messages))
        if self.current_index < len(self.scripted_responses):
            resp = self.scripted_responses[self.current_index]
            self.current_index += 1
        else:
            resp = self.scripted_responses[-1]
        return ChatResult(generations=[ChatGeneration(message=resp)])

    @property
    def _llm_type(self) -> str:
        return "scripted_mock"

    def bind_tools(
        self,
        tools: Sequence[Any],
        **kwargs: Any,
    ) -> Any:
        return self


def test_mini_agent_direct_response() -> None:
    """Verify agent directly returns response when no tools are requested."""
    model = ScriptedChatModel(
        scripted_responses=[AIMessage(content="Hello! How can I help you today?")]
    )
    agent = MiniAgent(model=model, tools=[calculator])

    result = agent.run("Hello")
    assert result == "Hello! How can I help you today?"


def test_mini_agent_single_tool_execution() -> None:
    """Verify agent calls a tool, gets observation, and returns final answer."""
    model = ScriptedChatModel(
        scripted_responses=[
            AIMessage(
                content="I need to calculate this.",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": "12 * 12"},
                        "id": "calc_call_1",
                    }
                ],
            ),
            AIMessage(content="The result of 12 * 12 is 144."),
        ]
    )
    agent = MiniAgent(model=model, tools=[calculator])

    steps = list(agent.stream_run("What is 12 * 12?"))
    step_types = [s.step_type for s in steps]

    assert AgentStepType.THOUGHT in step_types
    assert AgentStepType.TOOL_CALL in step_types
    assert AgentStepType.OBSERVATION in step_types
    assert AgentStepType.FINAL_ANSWER in step_types

    final_step = [s for s in steps if s.step_type == AgentStepType.FINAL_ANSWER][0]
    assert "144" in final_step.content


def test_mini_agent_multi_step_reasoning() -> None:
    """Verify agent can execute multiple tools across iterations."""
    model = ScriptedChatModel(
        scripted_responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": "100 / 2"},
                        "id": "call_1",
                    }
                ],
            ),
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": "get_system_info",
                        "args": {"query_type": "os"},
                        "id": "call_2",
                    }
                ],
            ),
            AIMessage(content="Calculated 50 and retrieved host OS info successfully."),
        ]
    )
    agent = MiniAgent(model=model, tools=[calculator, get_system_info])

    result = agent.run("Perform calculation then check OS.")
    assert "50" in result
    assert "OS" in result


def test_mini_agent_max_iterations_guard() -> None:
    """Verify agent breaks loop and returns warning when max iterations reached."""
    # Model that continuously emits tool calls
    infinite_tool_caller = ScriptedChatModel(
        scripted_responses=[
            AIMessage(
                content="Still checking...",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": "1+1"},
                        "id": f"call_{i}",
                    }
                ],
            )
            for i in range(10)
        ]
    )
    agent = MiniAgent(
        model=infinite_tool_caller,
        tools=[calculator],
        max_iterations=3,
    )

    steps = list(agent.stream_run("Loop forever"))
    last_step = steps[-1]
    assert last_step.step_type == AgentStepType.MAX_ITERATIONS
    assert "maximum iterations limit (3)" in last_step.content


def test_mini_agent_memory_persistence(tmp_path: Path) -> None:
    """Verify MiniAgent stores and recalls history across multiple invocations."""
    store = FileHistoryStore(storage_dir=tmp_path, max_messages_per_session=10)

    model = ScriptedChatModel(
        scripted_responses=[
            AIMessage(content="Nice to meet you, Alice!"),
            AIMessage(content="Your name is Alice!"),
        ]
    )
    agent = MiniAgent(
        model=model,
        tools=[calculator],
        history_store=store,
    )

    # Turn 1
    res1 = agent.run("My name is Alice", session_id="user_alice")
    assert res1 == "Nice to meet you, Alice!"

    # Verify history on disk
    history = store.get_history("user_alice").messages
    assert len(history) == 2
    assert history[0].content == "My name is Alice"
    assert history[1].content == "Nice to meet you, Alice!"

    # Turn 2
    res2 = agent.run("What is my name?", session_id="user_alice")
    assert res2 == "Your name is Alice!"

    history_after = store.get_history("user_alice").messages
    assert len(history_after) == 4

    # Verify that in turn 2, the model received prior history in its prompt
    second_call_messages = model.received_message_history[1]
    msg_contents = [m.content for m in second_call_messages]
    assert "My name is Alice" in msg_contents
    assert "Nice to meet you, Alice!" in msg_contents


def test_mini_agent_runnable_interface() -> None:
    """Verify MiniAgent complies with LCEL Runnable invoke and stream protocols."""
    model = ScriptedChatModel(
        scripted_responses=[AIMessage(content="Runnable invocation output.")]
    )
    agent = MiniAgent(model=model, tools=[calculator])

    # Synchronous invoke
    out_invoke = agent.invoke({"input": "test query"})
    assert out_invoke == "Runnable invocation output."

    # Streaming chunks
    chunks = list(agent.stream({"input": "test streaming"}))
    assert len(chunks) == 1
    assert chunks[0].step_type == AgentStepType.FINAL_ANSWER
    assert chunks[0].content == "Runnable invocation output."
