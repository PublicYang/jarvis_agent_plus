"""Terminal output formatting and step renderers for Jarvis Agent Plus."""

from rich.console import Console

from runtime import AgentStep, AgentStepType


class StepRenderer:
    """Helper to render agent execution events and real-time streaming tokens."""

    def __init__(self, console: Console) -> None:
        self.console = console
        self.in_token_stream = False
        self.has_printed_tokens = False

    def render(self, step: AgentStep) -> None:
        """Render a single AgentStep to the terminal."""
        if step.step_type == AgentStepType.TOKEN:
            if not self.in_token_stream:
                self.console.print("[bold green]Jarvis:[/bold green] ", end="")
                self.in_token_stream = True
                self.has_printed_tokens = True
            print(step.content, end="", flush=True)

        elif step.step_type == AgentStepType.THOUGHT:
            if self.in_token_stream:
                print()
                self.in_token_stream = False
            self.has_printed_tokens = False
            self.console.print(f"[dim italic]Thinking: {step.content}[/dim italic]")

        elif step.step_type == AgentStepType.TOOL_CALL:
            if self.in_token_stream:
                print()
                self.in_token_stream = False
            self.has_printed_tokens = False
            name = step.metadata.get("name", "unknown")
            args = step.metadata.get("args", {})
            self.console.print(f"[bold blue]Action:[/bold blue] {name}({args})")

        elif step.step_type == AgentStepType.OBSERVATION:
            if self.in_token_stream:
                print()
                self.in_token_stream = False
            self.console.print(f"[dim cyan]Observation:[/dim cyan] {step.content}")

        elif step.step_type == AgentStepType.FINAL_ANSWER:
            if self.in_token_stream:
                print()
                self.in_token_stream = False
            elif not self.has_printed_tokens:
                self.console.print(f"[bold green]Jarvis:[/bold green] {step.content}")

        elif step.step_type == AgentStepType.MAX_ITERATIONS:
            if self.in_token_stream:
                print()
                self.in_token_stream = False
            self.console.print(f"[bold red]Warning:[/bold red] {step.content}")
