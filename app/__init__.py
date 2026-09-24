"""Application Layer.

Contains CLI interaction, Typer commands, and terminal rendering for Jarvis Agent Plus.
"""

from app.cli import app
from app.main import run

__all__: list[str] = ["app", "run"]
