"""Typer CLI interface and commands for Jarvis Agent Plus."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llm import get_chat_model
from memory import InMemoryHistoryStore
from prompts import create_chat_prompt, get_string_parser
from runtime import (
    compose_sequence,
    create_stateful_chain,
    stream_text,
    stream_with_session,
)
from tools import ALL_TOOLS

app = typer.Typer(
    name="jarvis",
    help="Jarvis Agent Plus - LangChain Edition CLI",
    add_completion=False,
)
console = Console()


@app.command()
def ask(
    query: str = typer.Argument(..., help="The query or prompt to ask Jarvis"),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Model name (defaults to OPENAI_MODEL_NAME or gpt-4o-mini)",
    ),
    temperature: float = typer.Option(
        0.0, "--temperature", "-t", help="Sampling temperature"
    ),
) -> None:
    """Send a prompt through the LCEL pipeline with typewriter streaming output."""
    chat_model = get_chat_model(
        model_name=model,
        temperature=temperature,
        streaming=True,
    )
    actual_model = getattr(chat_model, "model_name", model or "gpt-4o-mini")

    console.print(
        Panel.fit(
            f"[bold cyan]Query:[/bold cyan] {query}\n"
            f"[dim]Model: {actual_model} | Temperature: {temperature}[/dim]",
            title="Jarvis Agent Plus",
            border_style="cyan",
        )
    )

    prompt = create_chat_prompt(
        system_prompt="You are Jarvis Agent Plus, an expert AI assistant."
    )
    parser = get_string_parser()
    chain = compose_sequence(prompt, chat_model, parser)

    console.print("[bold green]Jarvis:[/bold green] ", end="")
    try:
        for chunk in stream_text(chain, {"input": query}):
            print(chunk, end="", flush=True)
        print()
    except Exception as exc:
        console.print(f"\n[bold red]Error running chain:[/bold red] {exc}")
        console.print(
            "[dim yellow]Tip: Ensure OPENAI_API_KEY is configured.[/dim yellow]"
        )


@app.command()
def chat(
    session_id: str = typer.Option(
        "default",
        "--session-id",
        "-s",
        help="Session identifier for conversation memory",
    ),
    model: str | None = typer.Option(
        None,
        "--model",
        "-m",
        help="Model name (defaults to OPENAI_MODEL_NAME or gpt-4o-mini)",
    ),
    temperature: float = typer.Option(
        0.0, "--temperature", "-t", help="Sampling temperature"
    ),
    max_history: int = typer.Option(
        10, "--max-history", help="Maximum messages to retain in window"
    ),
) -> None:
    """Start an interactive multi-turn chat session with stateful memory."""
    chat_model = get_chat_model(
        model_name=model,
        temperature=temperature,
        streaming=True,
    )
    actual_model = getattr(chat_model, "model_name", model or "gpt-4o-mini")

    console.print(
        Panel.fit(
            f"[bold cyan]Interactive Chat Mode[/bold cyan]\n"
            f"[dim]Session: {session_id} | Model: {actual_model}[/dim]\n"
            f"[dim]Max History: {max_history}[/dim]\n"
            f"[dim]Commands: 'exit'/'quit' to end, 'clear' to reset.[/dim]",
            title="Jarvis Agent Plus - Memory",
            border_style="green",
        )
    )

    prompt = create_chat_prompt(
        system_prompt="You are Jarvis Agent Plus, an expert AI assistant.",
        history_key="chat_history",
    )
    parser = get_string_parser()
    chain = compose_sequence(prompt, chat_model, parser)

    store = InMemoryHistoryStore(max_messages_per_session=max_history)
    stateful_chain = create_stateful_chain(
        runnable=chain,
        get_session_history=store.get_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )

    while True:
        try:
            user_input = typer.prompt("[User]")
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break

        cleaned = user_input.strip()
        if not cleaned:
            continue
        if cleaned.lower() in ("exit", "quit"):
            console.print("[dim]Goodbye![/dim]")
            break
        if cleaned.lower() == "clear":
            store.clear_session(session_id)
            console.print("[yellow]Session history cleared.[/yellow]")
            continue

        console.print("[bold green]Jarvis:[/bold green] ", end="")
        try:
            for chunk in stream_with_session(
                stateful_chain, cleaned, session_id=session_id
            ):
                print(chunk, end="", flush=True)
            print()
        except Exception as exc:
            console.print(f"\n[bold red]Error running chain:[/bold red] {exc}")
            console.print(
                "[dim yellow]Tip: Ensure OPENAI_API_KEY is configured.[/dim yellow]"
            )


@app.command()
def tools() -> None:
    """List all registered tools available in the Jarvis environment."""
    table = Table(
        title="Registered Tools in Jarvis Agent Plus",
        border_style="blue",
    )
    table.add_column("Tool Name", style="bold cyan")
    table.add_column("Description", style="white")
    table.add_column("Parameters Schema", style="dim")

    for tool_item in ALL_TOOLS:
        schema = tool_item.args_schema.model_json_schema()
        param_desc = ", ".join(
            f"{k}: {v.get('type', 'any')}"
            for k, v in schema.get("properties", {}).items()
        )
        table.add_row(tool_item.name, tool_item.description, param_desc)

    console.print(table)
