"""Mathematical calculator tool definition."""

import ast
import operator
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

# Allowed binary operators for safe mathematical evaluation
SAFE_OPERATORS: dict[type[ast.operator], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.FloorDiv: operator.floordiv,
}


def safe_eval(node: ast.AST) -> float | int:
    """Recursively evaluate an AST expression safely without code execution."""
    if isinstance(node, ast.Expression):
        return safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
        return node.value
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub):
        return -safe_eval(node.operand)
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in SAFE_OPERATORS:
            left = safe_eval(node.left)
            right = safe_eval(node.right)
            return SAFE_OPERATORS[op_type](left, right)
    raise ValueError(f"Unsupported mathematical syntax: {ast.dump(node)}")


class CalculatorInput(BaseModel):
    """Input schema for calculator tool."""

    expression: str = Field(
        description="The mathematical expression to evaluate, e.g., '2 + 2' or '10 * 5'"
    )


@tool("calculator", args_schema=CalculatorInput)
def calculator(expression: str) -> str:
    """Calculate the result of a mathematical expression safely."""
    try:
        parsed = ast.parse(expression.strip(), mode="eval")
        result = safe_eval(parsed)
        return str(result)
    except Exception as exc:
        return f"Error evaluating expression '{expression}': {exc}"
