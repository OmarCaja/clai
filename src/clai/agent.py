from langchain.chat_models import init_chat_model
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from clai.tools import run_shell_command

SYSTEM_PROMPT = "You are clai, a helpful command-line assistant. Answer concisely."

TOOLS = [run_shell_command]
TOOLS_BY_NAME = {tool.name: tool for tool in TOOLS}


def ask(request: str, model_name: str) -> str:
    """Answer a natural-language request, running shell commands when needed."""

    model = init_chat_model(model=model_name).bind_tools(TOOLS)

    conversation: list[BaseMessage] = [
        SystemMessage(SYSTEM_PROMPT),
        HumanMessage(request),
    ]

    response = model.invoke(conversation)

    conversation.append(response)

    for tool_call in response.tool_calls:
        tool = TOOLS_BY_NAME[tool_call["name"]]
        tool_result = tool.invoke(tool_call)
        conversation.append(tool_result)

    if response.tool_calls:
        response = model.invoke(conversation)

    return response.text
