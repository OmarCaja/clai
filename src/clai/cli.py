"""The `clai` command: parse arguments, build the agent, answer the request."""

import argparse
import os
import sys
from importlib.metadata import version

from clai.agent import make_agent
from clai.chat import EXIT_COMMAND, chat
from clai.console import print_answer, show_error

DEFAULT_MODEL = "google_genai:gemini-2.5-flash-lite"


def main() -> None:
    """Entry point, installed as the `clai` script by pyproject.toml."""
    args = parse_args()
    try:
        agent = make_agent(args.model)
    # Unknown provider, missing API key, missing package: each raises differently.
    except Exception as error:  # noqa: BLE001
        show_error(f"Could not load model '{args.model}': {error}")
        sys.exit(1)

    request = " ".join(args.request)
    if request and not print_answer(agent, request) and not args.interactive:
        sys.exit(1)

    if args.interactive:
        chat(agent)


def parse_args() -> argparse.Namespace:
    """Read the command line; exits with a usage message if it is invalid."""
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
        help="keep chatting; the agent remembers earlier turns. "
        f"Type '{EXIT_COMMAND}' or press Ctrl-D to quit",
    )

    args = parser.parse_args()
    if not args.interactive and not args.request:
        parser.error("a request is required unless you use --interactive")
    return args
