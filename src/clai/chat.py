"""Interactive mode (`clai -i`): keep answering requests, with line history."""

import contextlib
import readline  # Importing it also gives input() arrow keys and line editing.
from pathlib import Path

from clai.agent import Agent
from clai.console import console, print_answer

EXIT_COMMAND = "exit"
HISTORY_FILE = Path.home() / ".clai" / ".clai_history"
HISTORY_LENGTH = 1000
# Given to input() itself, not printed by rich, so readline knows where the line
# starts and redraws recalled requests in the right place. Plain on purpose:
# macOS libedit miscounts colour codes in the prompt.
PROMPT = "> "


def chat(agent: Agent) -> None:
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


def load_history() -> None:
    """Let the up arrow recall requests from earlier interactive sessions."""
    # Add only requests by hand, so y/n answers to prompts stay out of history.
    readline.set_auto_history(False)
    readline.set_history_length(HISTORY_LENGTH)
    with contextlib.suppress(FileNotFoundError):
        readline.read_history_file(HISTORY_FILE)


def save_history() -> None:
    """Write the history file, ignoring failures."""
    # Losing history is not worth failing over (e.g. a read-only home folder).
    with contextlib.suppress(OSError):
        readline.write_history_file(HISTORY_FILE)
