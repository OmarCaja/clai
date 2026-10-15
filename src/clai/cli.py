import argparse
import os

from langgraph.graph.state import CompiledStateGraph

from clai.agent import ask, make_agent
from clai.safety import is_read_only

DEFAULT_MODEL = "google_genai:gemini-2.5-flash-lite"


def ask_user(command: str) -> bool:
    answer = input(f"$ {command}\nRun this command? [y/N] ")
    return answer.strip().lower() == "y"


def confirm(command: str) -> bool:
    if is_read_only(command):
        print(f"$ {command} (auto-approved)")
        return True
    return ask_user(command)


def print_answer(agent: CompiledStateGraph, request: str) -> None:
    for chunk in ask(agent, request):
        print(chunk, end="", flush=True)
    print()


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
        help="Run in interactive mode, keep chatting; the agent remembers earlier turns",
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
        while True:
            try:
                line = input("> ")
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if not line.strip():
                continue
            print_answer(agent, line)
