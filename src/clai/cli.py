import argparse

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


def main() -> None:
    parser = argparse.ArgumentParser(prog="clai", description="Ask your terminal in plain words.")
    parser.add_argument("request", nargs="+", help='e.g. "explain me last commit"')
    args = parser.parse_args()

    request = " ".join(args.request)

    model = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

    conversation = [
        SystemMessage("You are clai, a helpful command-line assistant. Answer concisely."),
        HumanMessage(request),
    ]

    response = model.invoke(conversation)

    print(response.text)
