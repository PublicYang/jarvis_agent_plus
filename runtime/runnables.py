"""LCEL Runnable primitives and pipeline composition utilities."""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import (
    Runnable,
    RunnableLambda,
    RunnableParallel,
    RunnablePassthrough,
)


def make_lambda[T, R](
    func: Callable[[T], R], name: str | None = None
) -> RunnableLambda:
    """Wrap a pure Python callable into a standard RunnableLambda."""
    return RunnableLambda(func, name=name)


def compose_sequence(*runnables: Runnable[Any, Any]) -> Runnable[Any, Any]:
    """Compose multiple Runnables sequentially using the LCEL pipe operator '|'."""
    if not runnables:
        raise ValueError("At least one Runnable must be provided to compose a sequence")
    chain = runnables[0]
    for step in runnables[1:]:
        chain = chain | step
    return chain


def compose_parallel(
    branches: dict[str, Runnable[Any, Any] | Callable[[Any], Any]],
) -> RunnableParallel:
    """Compose multiple independent Runnables or callables to execute in parallel.

    Returns a dict mapping each key to its branch's output.
    """
    return RunnableParallel(branches)


def assign_context(
    **assign_kwargs: Runnable[Any, Any] | Callable[[Any], Any],
) -> Runnable:
    """Return a RunnablePassthrough that assigns extra fields to a dict input."""
    return RunnablePassthrough.assign(**assign_kwargs)
