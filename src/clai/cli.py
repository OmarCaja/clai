import argparse
import contextlib
import os
import readline  # Importing it also gives input() arrow keys and line editing.
import sys
from importlib.metadata import version
from pathlib import Path

from langgraph.graph.state import CompiledStateGraph
from pydantic import ValidationError
from rich.console import Console
from rich.prompt import Confirm

from clai.agent import ask, make_agent
from clai.render import MarkdownStream
from clai.safety import is_read_only

DEFAULT_MODEL = "google_genai:gemini-2.5-flash-lite"
EXIT_COMMAND = "exit"
HISTORY_FILE = Path.home() / ".clai" / ".clai_history"
HISTORY_LENGTH = 1000
# Given to input() itself, not printed by rich, so readline knows where the line
# starts and redraws recalled requests in the right place. Plain on purpose:
# macOS libedit miscounts colour codes in the prompt.
PROMPT = "> "

console = Console()
answer = MarkdownStream(console)


def show_command(command: str, note: str = "") -> None:
    # markup=False: commands often contain [brackets] that rich would parse.
    console.print(f"$ {command}{note}", style="bold yellow", markup=False)


def show_error(message: str) -> None:
    console.print(f"Error: {message}", style="bold red", markup=False)


def summarize(error: Exception) -> str:
    """The useful part of a library error, without its long details."""
    if isinstance(error, ValidationError):
        # e.g. a missing API key, reported when the chat model is created.
        return str(error.errors()[0]["msg"]).removeprefix("Value error, ")
    return str(error).splitlines()[0]


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


def print_answer(agent: CompiledStateGraph, request: str) -> bool:
    """Stream the answer to a request. Returns False if it failed or was stopped."""
    try:
        with answer:
            for chunk in ask(agent, request):
                answer.write(chunk)
    except KeyboardInterrupt:
        console.print("Stopped.", style="dim")
        return False
    # Each provider raises its own errors; any failure ends only this request.
    except Exception as error:  # noqa: BLE001
        show_error(f"The request failed: {summarize(error)}")
        return False
    return True


def load_history() -> None:
    """Let the up arrow recall requests from earlier interactive sessions."""
    # Add only requests by hand, so y/n answers to prompts stay out of history.
    readline.set_auto_history(False)
    readline.set_history_length(HISTORY_LENGTH)
    with contextlib.suppress(FileNotFoundError):
        readline.read_history_file(HISTORY_FILE)


def save_history() -> None:
    # Losing history is not worth failing over (e.g. a read-only home folder).
    with contextlib.suppress(OSError):
        readline.write_history_file(HISTORY_FILE)


def chat(agent: CompiledStateGraph) -> None:
    """Keep answering requests until the user types `exit` or presses Ctrl-D."""
    console.print(f"Type '{EXIT_COMMAND}' or press Ctrl-D to quit.", style="dim")
    load_history()
    try:
        while True:
            try:
                line = input(PROMPT).strip()
            except (EOFError, KeyboardInterrupt):
                console.print()
                return
            if line.lower() == EXIT_COMMAND:
                return
            if line:
                readline.add_history(line)
                print_answer(agent, line)
    finally:
        save_history()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clai", description="Ask your terminal in plain words."
    )

    parser.add_argument(
        "-V", "--version", action="version", version=f"%(prog)s {version('clai')}"
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

    try:
        agent = make_agent(args.model, confirm)
    # Unknown provider, missing API key, missing package: each raises differently.
    except Exception as error:  # noqa: BLE001
        show_error(f"Could not load model '{args.model}': {summarize(error)}")
        sys.exit(1)

    request = " ".join(args.request)

    if request and not print_answer(agent, request) and not args.interactive:
        sys.exit(1)

    if args.interactive:
        chat(agent)
