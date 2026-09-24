"""Infrastructure and environment smoke tests for Jarvis Agent Plus."""

import importlib
import sys


def test_python_version() -> None:
    """Ensure Python runtime version meets the minimum requirement of >= 3.12."""
    assert sys.version_info >= (
        3,
        12,
    ), f"Python 3.12+ required, but running on {sys.version}"


def test_module_imports() -> None:
    """Ensure all core architectural modules can be imported without side effects."""
    modules = [
        "app",
        "llm",
        "prompts",
        "tools",
        "runtime",
        "memory",
    ]
    for mod_name in modules:
        mod = importlib.import_module(mod_name)
        assert hasattr(mod, "__all__"), f"Module {mod_name} must define __all__"
        assert isinstance(
            mod.__all__, list
        ), f"Module {mod_name}.__all__ must be a list"
