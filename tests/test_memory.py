"""Tests for memory layer, chat message history, and stateful LCEL chains."""

from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage

from memory import (
    FileChatMessageHistory,
    InMemoryHistoryStore,
    WindowedChatMessageHistory,
    trim_chat_history,
)
from prompts import create_chat_prompt
from runtime import (
    compose_sequence,
    create_stateful_chain,
    invoke_with_session,
    make_lambda,
    stream_with_session,
)


def test_windowed_chat_message_history() -> None:
    """Verify windowed chat message history respects max_messages sliding window."""
    history = WindowedChatMessageHistory(max_messages=3)
    assert history.messages == []

    history.add_user_message("msg 1")
    history.add_ai_message("msg 2")
    history.add_user_message("msg 3")
    assert len(history.messages) == 3
    assert history.messages[0].content == "msg 1"

    # Adding a 4th message should slide the window to retain only the last 3
    history.add_ai_message("msg 4")
    assert len(history.messages) == 3
    assert [m.content for m in history.messages] == ["msg 2", "msg 3", "msg 4"]

    history.clear()
    assert history.messages == []


def test_trim_chat_history_utility() -> None:
    """Verify standalone trim_chat_history trims correctly."""
    messages = [HumanMessage(content=f"m{i}") for i in range(10)]
    trimmed = trim_chat_history(messages, max_messages=4)
    assert len(trimmed) == 4
    assert [m.content for m in trimmed] == ["m6", "m7", "m8", "m9"]

    # If length <= max_messages, return all
    short = trim_chat_history(messages[:3], max_messages=5)
    assert len(short) == 3


def test_file_chat_message_history(tmp_path: Path) -> None:
    """Verify file-backed chat message history persists to disk in JSON format."""
    history = FileChatMessageHistory(
        session_id="test_sess",
        storage_dir=tmp_path,
        max_messages=2,
    )
    assert history.messages == []

    history.add_user_message("hello disk")
    history.add_ai_message("hello user")
    assert len(history.messages) == 2

    # Verify new instance with same path reads persisted state
    history_reloaded = FileChatMessageHistory(
        session_id="test_sess",
        storage_dir=tmp_path,
        max_messages=2,
    )
    assert len(history_reloaded.messages) == 2
    assert history_reloaded.messages[0].content == "hello disk"

    # Add 3rd message and verify sliding window on disk
    history_reloaded.add_user_message("third message")
    assert len(history_reloaded.messages) == 2
    assert [m.content for m in history_reloaded.messages] == [
        "hello user",
        "third message",
    ]

    history_reloaded.clear()
    assert history_reloaded.messages == []


def test_in_memory_history_store() -> None:
    """Verify InMemoryHistoryStore provides isolated session histories."""
    store = InMemoryHistoryStore(max_messages_per_session=5)

    hist_a = store.get_history("session_a")
    hist_b = store.get_history("session_b")

    hist_a.add_user_message("user in A")
    hist_b.add_user_message("user in B")

    assert len(hist_a.messages) == 1
    assert hist_a.messages[0].content == "user in A"
    assert len(hist_b.messages) == 1
    assert hist_b.messages[0].content == "user in B"

    assert set(store.list_sessions()) == {"session_a", "session_b"}

    store.clear_session("session_a")
    assert "session_a" not in store.list_sessions()
    assert len(store.get_history("session_a").messages) == 0


def test_stateful_chain_multi_turn_and_isolation() -> None:
    """Verify RunnableWithMessageHistory integrates with LCEL and isolates sessions."""
    prompt = create_chat_prompt(
        system_prompt="You are a mock assistant.",
        history_key="chat_history",
    )

    def mock_agent_step(prompt_val: Any) -> str:
        history_count = len(prompt_val.to_messages()) - 2  # subtract system & human
        user_msg = prompt_val.to_messages()[-1].content
        return f"Echo ({history_count} prior): {user_msg}"

    chain = compose_sequence(prompt, make_lambda(mock_agent_step))
    store = InMemoryHistoryStore()

    stateful = create_stateful_chain(
        runnable=chain,
        get_session_history=store.get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    # Turn 1 on session_1
    res1 = invoke_with_session(stateful, "My name is Bob", session_id="session_1")
    assert res1 == "Echo (0 prior): My name is Bob"
    history_s1 = store.get_history("session_1").messages
    assert len(history_s1) == 2
    assert isinstance(history_s1[0], HumanMessage)
    assert isinstance(history_s1[1], AIMessage)

    # Turn 2 on session_1 (should see 2 prior messages in prompt)
    res2 = invoke_with_session(stateful, "What is my name?", session_id="session_1")
    assert res2 == "Echo (2 prior): What is my name?"
    assert len(store.get_history("session_1").messages) == 4

    # Turn 1 on session_2 (should be completely isolated with 0 prior messages)
    res3 = invoke_with_session(stateful, "Hello from Eve", session_id="session_2")
    assert res3 == "Echo (0 prior): Hello from Eve"
    assert len(store.get_history("session_2").messages) == 2


def test_stateful_chain_streaming() -> None:
    """Verify stream_with_session emits chunks and records history correctly."""
    prompt = create_chat_prompt(
        system_prompt="System prompt.",
        history_key="chat_history",
    )

    def stream_generator(prompt_val: Any):
        yield "Streamed "
        yield "Response"

    chain = compose_sequence(prompt, make_lambda(stream_generator))
    store = InMemoryHistoryStore()
    stateful = create_stateful_chain(
        runnable=chain,
        get_session_history=store.get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    chunks = list(
        stream_with_session(stateful, "Test Stream Input", session_id="stream_sess")
    )
    assert "".join(chunks) == "Streamed Response"

    # History should contain the user input and the aggregated stream response
    history = store.get_history("stream_sess").messages
    assert len(history) == 2
    assert history[0].content == "Test Stream Input"
    assert history[1].content == "Streamed Response"
