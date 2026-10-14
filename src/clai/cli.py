import argparse
import os

from clai.agent import ask

DEFAULT_MODEL = "google_genai:gemini-2.5-flash-lite"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="clai", description="Ask your terminal in plain words."
    )

    parser.add_argument("request", nargs="+", help='e.g. "explain me last commit"')
    parser.add_argument(
        "-m",
        "--model",
        default=os.environ.get("CLAI_MODEL", DEFAULT_MODEL),
        help="provider: model to use (default: %(default)s)",
    )

    args = parser.parse_args()

    request = " ".join(args.request)

    print(ask(request, args.model))
