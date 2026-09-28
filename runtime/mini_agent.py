"""Mini-Agent ReAct runtime implementation based on pure LCEL and tool binding."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.tools import BaseTool

from runtime.tool_caller import bind_model_tools, execute_tool_calls, has_tool_calls


class AgentStepType(StrEnum):
    """Categorization for agent execution trace events."""

    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"
    FINAL_ANSWER = "final_answer"
    MAX_ITERATIONS = "max_iterations"


@dataclass
class AgentStep:
    """A single execution event in the MiniAgent ReAct cycle."""

    step_type: AgentStepType
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class MiniAgent(Runnable[dict[str, Any] | str, str]):
    """Compact ReAct Agent runtime orchestrator.

    Integrates ChatModel tool binding, observation feedback loop,
    sliding session memory, and dead-lock guard.
    """

    def __init__(
        self,
        model: BaseChatModel,
        tools: Sequence[BaseTool],
        system_prompt: str = (
            "You are Jarvis Agent Plus, an expert AI assistant equipped with tools."
        ),
        max_iterations: int = 5,
        history_store: Any | None = None,
    ) -> None:
        super().__init__()
        self.model = model
        self.tools = list(tools)
        self.tool_map: dict[str, BaseTool] = {t.name: t for t in self.tools}
        self.system_prompt = system_prompt
        self.max_iterations = max_iterations
        self.history_store = history_store

        # Compile LCEL bound model
        if self.tools:
            self.bound_model = bind_model_tools(self.model, self.tools)
        else:
            self.bound_model = self.model

    def stream_run(
        self,
        query: str,
        session_id: str | None = None,
    ) -> Iterator[AgentStep]:
        """Execute ReAct loop yielding step-by-step trace events."""
        history: BaseChatMessageHistory | None = None
        prior_messages: list[BaseMessage] = []

        if self.history_store and session_id:
            history = self.history_store.get_history(session_id)
            prior_messages = history.messages

        messages: list[BaseMessage] = [SystemMessage(content=self.system_prompt)]
        messages.extend(prior_messages)
        messages.append(HumanMessage(content=query))

        iterations = 0

        while iterations < self.max_iterations:
            iterations += 1
            ai_message = self.bound_model.invoke(messages)
            if not isinstance(ai_message, AIMessage):
                ai_message = AIMessage(content=str(ai_message))

            if has_tool_calls(ai_message):
                if ai_message.content:
                    yield AgentStep(
                        step_type=AgentStepType.THOUGHT,
                        content=str(ai_message.content),
                    )

                for tc in ai_message.tool_calls:
                    yield AgentStep(
                        step_type=AgentStepType.TOOL_CALL,
                        content=f"Calling tool: {tc.get('name')}",
                        metadata=tc,
                    )

                tool_messages = execute_tool_calls(ai_message.tool_calls, self.tool_map)
                for tm in tool_messages:
                    yield AgentStep(
                        step_type=AgentStepType.OBSERVATION,
                        content=str(tm.content),
                        metadata={
                            "name": tm.name,
                            "tool_call_id": tm.tool_call_id,
                            "status": tm.status,
                        },
                    )

                messages.append(ai_message)
                messages.extend(tool_messages)
            else:
                final_answer = str(ai_message.content)
                yield AgentStep(
                    step_type=AgentStepType.FINAL_ANSWER,
                    content=final_answer,
                )
                if history:
                    history.add_user_message(query)
                    history.add_ai_message(final_answer)
                return

        fallback_msg = (
            f"Agent reached maximum iterations limit ({self.max_iterations}) "
            "without reaching a final answer."
        )
        yield AgentStep(
            step_type=AgentStepType.MAX_ITERATIONS,
            content=fallback_msg,
        )
        if history:
            history.add_user_message(query)
            history.add_ai_message(fallback_msg)

    def run(self, query: str, session_id: str | None = None) -> str:
        """Run the agent and return the final answer string."""
        final_text = ""
        for step in self.stream_run(query, session_id=session_id):
            if step.step_type in (
                AgentStepType.FINAL_ANSWER,
                AgentStepType.MAX_ITERATIONS,
            ):
                final_text = step.content
        return final_text

    def invoke(
        self,
        input: dict[str, Any] | str,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> str:
        """Invoke agent complying with the Runnable interface."""
        query = input if isinstance(input, str) else str(input.get("input", ""))
        session_id = None
        if config and "configurable" in config:
            session_id = config["configurable"].get("session_id")
        return self.run(query, session_id=session_id)

    def stream(
        self,
        input: dict[str, Any] | str,
        config: RunnableConfig | None = None,
        **kwargs: Any,
    ) -> Iterator[AgentStep]:
        """Stream trace events complying with the Runnable interface."""
        query = input if isinstance(input, str) else str(input.get("input", ""))
        session_id = None
        if config and "configurable" in config:
            session_id = config["configurable"].get("session_id")
        yield from self.stream_run(query, session_id=session_id)
