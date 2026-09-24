"""Output parsers and structured data validation utilities."""

from typing import Any

from langchain_core.output_parsers import (
    JsonOutputParser,
    PydanticOutputParser,
    StrOutputParser,
)
from pydantic import BaseModel


def get_string_parser() -> StrOutputParser:
    """Return a standard StrOutputParser for raw text responses."""
    return StrOutputParser()


def get_json_parser() -> JsonOutputParser:
    """Return a JsonOutputParser for extracting dictionary objects."""
    return JsonOutputParser()


def create_pydantic_parser[T: BaseModel](model_cls: type[T]) -> PydanticOutputParser[T]:
    """Create a PydanticOutputParser bound to the specified Pydantic schema model."""
    return PydanticOutputParser(pydantic_object=model_cls)


def extract_format_instructions(parser: Any) -> str:
    """Safely extract format instructions from any supported output parser."""
    if hasattr(parser, "get_format_instructions"):
        return parser.get_format_instructions()
    return ""
