import argparse
import os
import readline  # noqa: F401 Importing it gives input() arrow keys and history.

from langgraph.graph.state import CompiledStateGraph
from rich.console import Console
from rich.prompt import Confirm

from clai.agent import ask, make_agent
from clai.render import MarkdownStream
from clai.safety import is_read_only

DEFAULT_MODEL = "google_genai:gemini-2.5-flash-lite"
EXIT_COMMAND = "exit"

console = Console()
answer = MarkdownStream(console)


def show_command(command: str, note: str = "") -> None:
    # markup=False: commands often contain [brackets] that rich would parse.
    console.print(f"$ {command}{note}", style="bold yellow", markup=False)


def ask_user(command: str) -> bool:
    show_command(command)
    return Confirm.ask("Run this command?", default=False, console=console)


def confirm(command: str) -> bool:
    # The agent asks for a tool call mid-answer: stop redrawing the answer first.
    answer.close()
    if is_read_only(command):
        show_command(command, " (auto-approved)")
        return True
    return ask_user(command)


def print_answer(agent: CompiledStateGraph, request: str) -> None:
    with answer:
        for chunk in ask(agent, request):
            answer.write(chunk)


def chat(agent: CompiledStateGraph) -> None:
    """Keep answering requests until the user types `exit` or presses Ctrl-D."""
    console.print(f"Type '{EXIT_COMMAND}' or press Ctrl-D to quit.", style="dim")
    while True:
        try:
            line = console.input("[bold green]>[/] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print()
            return
        if line.lower() == EXIT_COMMAND:
            return
        if line:
            print_answer(agent, line)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clai", description="Ask your terminal in plain words."
    )

    parser.add_argument("request", nargs="*", help='e.g. "explain me last commit"')
    parser.add_argument(
        "-m",
        "--model",
        default=os.environ.get("CLAI_MODEL", DEFAULT_MODEL),
        help="provider:model to use (default: %(default)s)",
    )
    parser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        default=False,
        help="keep chatting; the agent remembers earlier turns. "
        f"Type '{EXIT_COMMAND}' or press Ctrl-D to quit",
    )

    args = parser.parse_args()

    if not args.interactive and not args.request:
        parser.error(
            "At least one request must be provided when running in non-interactive mode."
        )

    agent = make_agent(args.model, confirm)

    request = " ".join(args.request)

    if request:
        print_answer(agent, request)

    if args.interactive:
        chat(agent)
