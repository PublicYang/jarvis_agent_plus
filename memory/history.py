"""Chat message history implementations and session management."""

import json
from collections.abc import Sequence
from pathlib import Path

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import (
    BaseMessage,
    message_to_dict,
    messages_from_dict,
)


def trim_chat_history(
    messages: Sequence[BaseMessage],
    max_messages: int = 10,
) -> list[BaseMessage]:
    """Trim a list of messages to the most recent max_messages."""
    if len(messages) <= max_messages:
        return list(messages)
    return list(messages[-max_messages:])


class WindowedChatMessageHistory(BaseChatMessageHistory):
    """In-memory chat message history supporting sliding window truncation."""

    def __init__(self, max_messages: int | None = None) -> None:
        super().__init__()
        self._messages: list[BaseMessage] = []
        self.max_messages = max_messages

    @property
    def messages(self) -> list[BaseMessage]:
        return list(self._messages)

    @messages.setter
    def messages(self, messages: list[BaseMessage]) -> None:
        self._messages = list(messages)
        self._apply_window()

    def add_message(self, message: BaseMessage) -> None:
        self._messages.append(message)
        self._apply_window()

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        self._messages.extend(messages)
        self._apply_window()

    def clear(self) -> None:
        self._messages.clear()

    def _apply_window(self) -> None:
        if self.max_messages is not None and len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]


class FileChatMessageHistory(BaseChatMessageHistory):
    """File-backed chat message history stored in JSON format."""

    def __init__(
        self,
        session_id: str,
        storage_dir: str | Path = ".sessions",
        max_messages: int | None = None,
    ) -> None:
        super().__init__()
        self.session_id = session_id
        self.storage_dir = Path(storage_dir)
        self.max_messages = max_messages
        self.file_path = self.storage_dir / f"{session_id}.json"

    @property
    def messages(self) -> list[BaseMessage]:
        if not self.file_path.exists():
            return []
        try:
            with open(self.file_path, encoding="utf-8") as f:
                data = json.load(f)
            return messages_from_dict(data)
        except (json.JSONDecodeError, OSError):
            return []

    def add_message(self, message: BaseMessage) -> None:
        self.add_messages([message])

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        current_messages = self.messages
        current_messages.extend(messages)
        if self.max_messages is not None and len(current_messages) > self.max_messages:
            current_messages = current_messages[-self.max_messages :]

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        serialized = [message_to_dict(msg) for msg in current_messages]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, ensure_ascii=False, indent=2)

    def clear(self) -> None:
        if self.file_path.exists():
            self.file_path.unlink()


class InMemoryHistoryStore:
    """Session-isolated in-memory history store."""

    def __init__(self, max_messages_per_session: int | None = None) -> None:
        self.max_messages_per_session = max_messages_per_session
        self._store: dict[str, WindowedChatMessageHistory] = {}

    def get_history(self, session_id: str) -> WindowedChatMessageHistory:
        """Get or create chat history for the given session_id."""
        if session_id not in self._store:
            self._store[session_id] = WindowedChatMessageHistory(
                max_messages=self.max_messages_per_session
            )
        return self._store[session_id]

    def clear_session(self, session_id: str) -> bool:
        """Clear messages for a specific session."""
        if session_id in self._store:
            self._store[session_id].clear()
            del self._store[session_id]
            return True
        return False

    def list_sessions(self) -> list[str]:
        """Return all active session IDs."""
        return list(self._store.keys())

    def reset_all(self) -> None:
        """Reset all sessions."""
        self._store.clear()


class FileHistoryStore:
    """Session store backed by local JSON files."""

    def __init__(
        self,
        storage_dir: str | Path = ".sessions",
        max_messages_per_session: int | None = None,
    ) -> None:
        self.storage_dir = Path(storage_dir)
        self.max_messages_per_session = max_messages_per_session

    def get_history(self, session_id: str) -> FileChatMessageHistory:
        """Get or create file-backed chat history for the given session_id."""
        return FileChatMessageHistory(
            session_id=session_id,
            storage_dir=self.storage_dir,
            max_messages=self.max_messages_per_session,
        )

    def clear_session(self, session_id: str) -> bool:
        """Clear messages for a specific session."""
        target = self.storage_dir / f"{session_id}.json"
        if target.exists():
            target.unlink()
            return True
        return False

    def list_sessions(self) -> list[str]:
        """Return all active stored session IDs."""
        if not self.storage_dir.exists():
            return []
        return [f.stem for f in self.storage_dir.glob("*.json")]

    def reset_all(self) -> None:
        """Clear all stored sessions."""
        if self.storage_dir.exists():
            for f in self.storage_dir.glob("*.json"):
                f.unlink()

