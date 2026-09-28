"""Typer CLI interface and commands for Jarvis Agent Plus."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from llm import get_chat_model
from memory import FileHistoryStore
from runtime import AgentStep, AgentStepType, MiniAgent
from tools import ALL_TOOLS

app = typer.Typer(
    name="jarvis",
    help="Jarvis Agent Plus - LangChain Edition CLI",
    add_completion=False,
)
console = Console()


def _render_step(step: AgentStep) -> None:
    """Helper to render agent steps to the console."""
    if step.step_type == AgentStepType.THOUGHT:
        console.print(f"[dim italic]Thinking: {step.content}[/dim italic]")
    elif step.step_type == AgentStepType.TOOL_CALL:
        name = step.metadata.get("name", "unknown")
        args = step.metadata.get("args", {})
        console.print(f"[bold blue]Action:[/bold blue] {name}({args})")
    elif step.step_type == AgentStepType.OBSERVATION:
        console.print(f"[dim cyan]Observation:[/dim cyan] {step.content}")
    elif step.step_type == AgentStepType.FINAL_ANSWER:
        console.print(f"[bold green]Jarvis:[/bold green] {step.content}")
    elif step.step_type == AgentStepType.MAX_ITERATIONS:
        console.print(f"[bold red]Warning:[/bold red] {step.content}")


@app.command()
def ask(
    query: str = typer.Argument(..., help="The query or prompt to ask Jarvis"),
    session_id: str = typer.Option(
        "default",
        "--session-id",
        "-s",
        help="Session identifier for persistent conversation memory",
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
    max_iterations: int = typer.Option(
        5, "--max-iterations", help="Maximum ReAct reasoning steps"
    ),
) -> None:
    """Send a prompt to the MiniAgent with tools and persistent memory."""
    chat_model = get_chat_model(
        model_name=model,
        temperature=temperature,
        streaming=False,
    )
    actual_model = getattr(chat_model, "model_name", model or "gpt-4o-mini")

    console.print(
        Panel.fit(
            f"[bold cyan]Query:[/bold cyan] {query}\n"
            f"[dim]Model: {actual_model} | Session: {session_id} | "
            f"Tools: {len(ALL_TOOLS)}[/dim]",
            title="Jarvis Agent Plus - MiniAgent",
            border_style="cyan",
        )
    )

    store = FileHistoryStore(storage_dir=".sessions", max_messages_per_session=10)
    agent = MiniAgent(
        model=chat_model,
        tools=ALL_TOOLS,
        max_iterations=max_iterations,
        history_store=store,
    )

    try:
        for step in agent.stream_run(query, session_id=session_id):
            _render_step(step)
    except Exception as exc:
        console.print(f"\n[bold red]Error running agent:[/bold red] {exc}")
        console.print(
            "[dim yellow]Tip: Ensure OPENAI_API_KEY is configured.[/dim yellow]"
        )


@app.command()
def chat(
    session_id: str = typer.Option(
        "default",
        "--session-id",
        "-s",
        help="Session identifier for persistent conversation memory",
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
    max_iterations: int = typer.Option(
        5, "--max-iterations", help="Maximum ReAct reasoning steps per turn"
    ),
) -> None:
    """Start an interactive multi-turn session with MiniAgent, tools and memory."""
    chat_model = get_chat_model(
        model_name=model,
        temperature=temperature,
        streaming=False,
    )
    actual_model = getattr(chat_model, "model_name", model or "gpt-4o-mini")

    console.print(
        Panel.fit(
            f"[bold cyan]Interactive Agent Chat Mode[/bold cyan]\n"
            f"[dim]Session: {session_id} | Model: {actual_model}[/dim]\n"
            f"[dim]Max History: {max_history} | Tools: {len(ALL_TOOLS)}[/dim]\n"
            f"[dim]Commands: 'exit'/'quit' to end, 'clear' to reset.[/dim]",
            title="Jarvis Agent Plus - MiniAgent ReAct",
            border_style="green",
        )
    )

    store = FileHistoryStore(
        storage_dir=".sessions",
        max_messages_per_session=max_history,
    )
    agent = MiniAgent(
        model=chat_model,
        tools=ALL_TOOLS,
        max_iterations=max_iterations,
        history_store=store,
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

        try:
            for step in agent.stream_run(cleaned, session_id=session_id):
                _render_step(step)
        except Exception as exc:
            console.print(f"\n[bold red]Error running agent:[/bold red] {exc}")
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
