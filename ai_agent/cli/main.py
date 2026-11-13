from __future__ import annotations

import json
import sys
from typing import Any

from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table

from ..agent.loop import AgentLoop, AgentResult, Step

console = Console()


def _print_welcome() -> None:
    console.print(
        Panel(
            "[bold]Intentio[/bold]: workplace automation agent\n"
            "Type your request in plain English. Special commands: [dim]:help[/dim]  [dim]:history[/dim]  [dim]:exit[/dim]",
            border_style="dim",
        )
    )


def _print_help() -> None:
    console.print(
        Panel(
            "[bold]Commands[/bold]\n"
            "  [cyan]:help[/cyan]     show this message\n"
            "  [cyan]:history[/cyan]  show all steps from this session\n"
            "  [cyan]:exit[/cyan]     quit\n\n"
            "[bold]Example prompts[/bold]\n"
            "  Send a message to #engineering: deployment complete\n"
            "  Create a Jira ticket for the login bug, assign it to me, notify #backend-team\n"
            "  Show me my calendar events this week and find a free 2-hour slot",
            border_style="blue",
        )
    )


def _print_steps(result: AgentResult) -> None:
    if not result.steps:
        return

    table = Table(
        title="Actions taken",
        show_header=True,
        header_style="bold dim",
        border_style="dim",
        expand=False,
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Tool", style="cyan", no_wrap=True)
    table.add_column("Result", style="white")

    for i, step in enumerate(result.steps, 1):
        ok = step.output.get("ok", True)
        status = "[green]ok[/green]" if ok else "[red]error[/red]"
        summary = _summarise_output(step.output)
        table.add_row(str(i), escape(step.tool), f"{status}  {escape(summary)}")

    console.print(table)


def _summarise_output(output: dict[str, Any]) -> str:
    """One-line human-readable summary of a tool result."""
    if not output.get("ok", True):
        return str(output.get("error", "unknown error"))
    # Pick the most useful fields to show
    for key in ("key", "ts", "id", "slot", "total", "channel"):
        if key in output:
            val = output[key]
            if isinstance(val, dict):
                return json.dumps(val)
            return str(val)
    return "done"


def _print_answer(result: AgentResult) -> None:
    style = "yellow" if result.reached_limit else "green"
    console.print(Panel(result.final_answer, border_style=style, title="Agent"))


def run_cli(loop: AgentLoop) -> None:
    _print_welcome()
    session_steps: list[Step] = []

    while True:
        try:
            console.print()
            raw = console.input("[bold cyan]You >[/bold cyan] ").strip()
        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]bye[/dim]")
            sys.exit(0)

        if not raw:
            continue

        if raw == ":exit":
            console.print("[dim]bye[/dim]")
            sys.exit(0)

        if raw == ":help":
            _print_help()
            continue

        if raw == ":history":
            if not session_steps:
                console.print("[dim]no steps yet[/dim]")
            else:
                _print_steps(AgentResult(final_answer="", steps=session_steps))
            continue

        with console.status("[dim]thinking…[/dim]", spinner="dots"):
            result = loop.run(raw)

        session_steps.extend(result.steps)
        _print_steps(result)
        _print_answer(result)


def main() -> None:
    """Entry point wired up in pyproject.toml scripts."""
    from ..agent.loop import AgentLoop
    from ..agent.registry import ToolRegistry
    from ..config import Settings
    from ..llm.client import LLMClient
    from ..logging_setup import setup_logging
    from ..mocks.seed import seed_store
    from ..mocks.store import MockStore
    from ..tools.calendar import make_calendar_tools
    from ..tools.email import make_email_tools
    from ..tools.jira import make_jira_tools
    from ..tools.slack import make_slack_tools

    settings = Settings()  # type: ignore[call-arg]
    setup_logging(level=settings.log_level, log_file=settings.log_file)

    store = MockStore.create(
        slack_force_error=settings.slack_force_error,
        calendar_force_error=settings.calendar_force_error,
        jira_force_error=settings.jira_force_error,
        email_force_error=settings.email_force_error,
    )
    seed_store(store, current_user=settings.current_user)

    registry = ToolRegistry()
    registry.register_many(make_slack_tools(store.slack))
    registry.register_many(make_calendar_tools(store.calendar))
    registry.register_many(make_jira_tools(store.jira))
    registry.register_many(make_email_tools(store.email))

    llm = LLMClient(
        api_key=settings.anthropic_api_key,
        model=settings.anthropic_model,
    )

    loop = AgentLoop(
        llm=llm,
        registry=registry,
        max_iterations=settings.agent_max_iterations,
        current_user=settings.current_user,
    )

    run_cli(loop)
