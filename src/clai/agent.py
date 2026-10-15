from collections.abc import Callable, Iterator
from typing import Any, cast

from langchain.agents import create_agent
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph

from clai.tools import make_run_shell_command

SYSTEM_PROMPT = """You are clai, a command-line assistant that runs shell commands \
with the run_shell_command tool.
Use commands only to get facts about this machine, its files or its repositories.
For general knowledge questions, answer directly without running commands.
Work step by step: run a command, look at its output, then decide the next command.
Never guess about something you can check: if you need a file's contents, read it first.
Never ask the user to run commands; run them yourself.
When you have verified the facts, answer concisely."""
RECURSION_LIMIT = 21

# stream_mode="messages" yields (message chunk, metadata) pairs,
# but LangGraph's type hints don't say so.
MessageStream = Iterator[tuple[BaseMessage, dict[str, Any]]]


def make_agent(model_name: str, confirm: Callable[[str], bool]) -> CompiledStateGraph:
    """Create an agent that can run shell commands."""
    return create_agent(
        model_name,
        tools=[make_run_shell_command(confirm)],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )


def ask(agent: CompiledStateGraph, request: str) -> Iterator[str]:
    """Answer a natural-language request, running shell commands when needed."""

    answered = False

    try:
        stream = cast(
            MessageStream,
            agent.stream(
                {"messages": [{"role": "user", "content": request}]},
                RunnableConfig(
                    recursion_limit=RECURSION_LIMIT, configurable={"thread_id": "1"}
                ),
                stream_mode="messages",
            ),
        )
        for token, meta in stream:
            if meta["langgraph_node"] == "model" and token.text:
                answered = True
                yield token.text

    except GraphRecursionError:
        yield f"Stopped after {RECURSION_LIMIT} steps without a final answer."
        return

    if not answered:
        yield "The model returned an empty answer. Try again."
