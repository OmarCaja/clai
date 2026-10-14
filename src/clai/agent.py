from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from clai.tools import run_shell_command

SYSTEM_PROMPT = """You are clai, a command-line assistant that runs shell commands \
with the run_shell_command tool.
Use commands only to get facts about this machine, its files or its repositories.
For general knowledge questions, answer directly without running commands.
Work step by step: run a command, look at its output, then decide the next command.
Never guess about something you can check: if you need a file's contents, read it first.
Never ask the user to run commands; run them yourself.
When you have verified the facts, answer concisely."""
TOOLS = [run_shell_command]
TOOLS_BY_NAME = {tool.name: tool for tool in TOOLS}
MAX_STEPS = 10


def ask(request: str, model_name: str) -> str:
    """Answer a natural-language request, running shell commands when needed."""

    model = init_chat_model(model=model_name).bind_tools(TOOLS)

    conversation: list[BaseMessage] = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(request),
    ]

    for _ in range(MAX_STEPS):
        response = model.invoke(conversation)
        conversation.append(response)

        if not response.tool_calls:
            return response.text or "The model returned an empty answer. Try again."

        for tool_call in response.tool_calls:
            tool = TOOLS_BY_NAME[tool_call["name"]]
            conversation.append(tool.invoke(tool_call))

    return f"Stopped after {MAX_STEPS} steps without a final answer."
