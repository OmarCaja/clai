"""Everything clai shows in the terminal: answers, commands, prompts and errors."""

from rich.console import Console
from rich.prompt import Confirm

from clai.agent import Agent, ask

console = Console()


def show_command(command: str, note: str = "") -> None:
    """Print a command the agent wants to run, like a shell prompt."""
    # markup=False: commands often contain [brackets] that rich would parse.
    console.print(f"$ {command}{note}", style="bold yellow", markup=False)


def show_error(message: str) -> None:
    """Print an error in one red line."""
    console.print(f"Error: {message}", style="bold red", markup=False)


def confirm(command: str) -> bool:
    """Ask the user whether a command that needs review may run. Defaults to no."""
    show_command(command)
    return Confirm.ask("Run this command?", default=False, console=console)


def auto_approved(command: str) -> None:
    """Show a read-only command that runs without asking."""
    show_command(command, " (auto-approved)")


def print_answer(agent: Agent, request: str) -> bool:
    """Print the answer to a request. Returns False if it failed or was stopped."""
    try:
        # Plain text: Markdown in the answer is shown as written.
        print(ask(agent, request, confirm, auto_approved))
    except KeyboardInterrupt:
        console.print("Stopped.", style="dim")
        return False
    # Each provider raises its own errors; any failure ends only this request.
    except Exception as error:  # noqa: BLE001
        show_error(f"The request failed: {error}")
        return False
    return True
