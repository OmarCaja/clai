import argparse
import os

from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from clai.tools import run_shell_command

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
        help="provider:model to use (default: %(default)s)",
    )
    args = parser.parse_args()

    request = " ".join(args.request)

    tools = [run_shell_command]
    tools_by_name = {tool.name: tool for tool in tools}

    model = init_chat_model(model=args.model).bind_tools(tools)

    conversation: list[BaseMessage] = [
        SystemMessage(
            "You are clai, a helpful command-line assistant. Answer concisely."
        ),
        HumanMessage(request),
    ]

    response = model.invoke(conversation)

    conversation.append(response)

    for tool_call in response.tool_calls:
        tool = tools_by_name[tool_call["name"]]
        tool_result = tool.invoke(tool_call)
        conversation.append(tool_result)

    if response.tool_calls:
        response = model.invoke(conversation)

    print(response.text)
