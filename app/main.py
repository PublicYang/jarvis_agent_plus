"""Main entrypoint for Jarvis CLI application."""

from app.cli import app


def run() -> None:
    """Run the Typer application."""
    app()


if __name__ == "__main__":
    run()
