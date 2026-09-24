"""Typer CLI interface and commands for Jarvis Agent Plus."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llm import get_chat_model
from prompts import create_chat_prompt, get_string_parser
from runtime import compose_sequence, stream_text
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
    model: str = typer.Option("gpt-4o-mini", "--model", "-m", help="Model name"),
    temperature: float = typer.Option(
        0.0, "--temperature", "-t", help="Sampling temperature"
    ),
) -> None:
    """Send a prompt through the LCEL pipeline with typewriter streaming output."""
    console.print(
        Panel.fit(
            f"[bold cyan]Query:[/bold cyan] {query}\n"
            f"[dim]Model: {model} | Temperature: {temperature}[/dim]",
            title="Jarvis Agent Plus",
            border_style="cyan",
        )
    )

    prompt = create_chat_prompt(
        system_prompt="You are Jarvis Agent Plus, an expert AI assistant."
    )
    chat_model = get_chat_model(
        model_name=model,
        temperature=temperature,
        streaming=True,
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
