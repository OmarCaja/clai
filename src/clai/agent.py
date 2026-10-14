from langchain.agents import create_agent
from langchain_core.runnables import RunnableConfig
from langgraph.errors import GraphRecursionError

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
RECURSION_LIMIT = 21


def ask(request: str, model_name: str) -> str:
    """Answer a natural-language request, running shell commands when needed."""

    agent = create_agent(model_name, tools=TOOLS, system_prompt=SYSTEM_PROMPT)

    try:
        result = agent.invoke(
            {"messages": [{"role": "user", "content": request}]},
            RunnableConfig(recursion_limit=RECURSION_LIMIT),
        )
    except GraphRecursionError:
        return f"Stopped after {RECURSION_LIMIT} steps without a final answer."

    answer = result["messages"][-1].text
    return answer or "The model returned an empty answer. Try again."
