"""Tests for LCEL Runnable foundation and execution protocols."""

from collections.abc import Iterator

import pytest
from langchain_core.language_models.chat_models import BaseChatModel

from llm import get_chat_model
from runtime import (
    assign_context,
    compose_parallel,
    compose_sequence,
    make_lambda,
)


def test_get_chat_model_initialization() -> None:
    """Verify get_chat_model produces a valid BaseChatModel instance."""
    model = get_chat_model(model_name="gpt-4o-mini", temperature=0.7)
    assert isinstance(model, BaseChatModel)
    assert model.model_name == "gpt-4o-mini"
    assert model.temperature == 0.7


def test_runnable_invoke() -> None:
    """Test standard synchronous invoke protocol through an LCEL pipeline."""
    step1 = make_lambda(lambda x: {"count": x["count"] * 2})
    step2 = make_lambda(lambda x: f"Final: {x['count']}")
    chain = compose_sequence(step1, step2)

    result = chain.invoke({"count": 5})
    assert result == "Final: 10"


@pytest.mark.asyncio
async def test_runnable_ainvoke() -> None:
    """Test asynchronous ainvoke protocol through an LCEL pipeline."""
    step1 = make_lambda(lambda text: text.strip().upper())
    step2 = make_lambda(lambda text: f"Processed: {text}")
    chain = compose_sequence(step1, step2)

    result = await chain.ainvoke("  hello world  ")
    assert result == "Processed: HELLO WORLD"


def test_runnable_batch() -> None:
    """Test parallel batching protocol across multiple inputs."""
    step = make_lambda(lambda n: n**2)
    chain = compose_sequence(step)

    inputs = [1, 2, 3, 4, 5]
    results = chain.batch(inputs)
    assert results == [1, 4, 9, 16, 25]


def test_runnable_stream() -> None:
    """Test streaming chunk protocol through a generator-based Runnable."""

    def token_generator(prompt: str) -> Iterator[str]:
        for word in prompt.split():
            yield word + " "

    streamer = make_lambda(token_generator)
    chunks = list(streamer.stream("LangChain LCEL streaming verification"))
    assert "".join(chunks) == "LangChain LCEL streaming verification "


def test_runnable_parallel() -> None:
    """Test RunnableParallel multi-branch execution and dictionary aggregation."""
    parallel_chain = compose_parallel(
        {
            "double": make_lambda(lambda x: x["val"] * 2),
            "triple": make_lambda(lambda x: x["val"] * 3),
            "square": make_lambda(lambda x: x["val"] ** 2),
        }
    )

    output = parallel_chain.invoke({"val": 4})
    assert output == {
        "double": 8,
        "triple": 12,
        "square": 16,
    }


def test_runnable_passthrough_assign() -> None:
    """Test assigning dynamic context while preserving original inputs."""
    chain = compose_sequence(
        assign_context(
            length=make_lambda(lambda x: len(x["text"])),
            is_loud=make_lambda(lambda x: x["text"].isupper()),
        )
    )

    result = chain.invoke({"text": "HELLO"})
    assert result == {
        "text": "HELLO",
        "length": 5,
        "is_loud": True,
    }
