from collections.abc import Callable, Iterator
from typing import Any, cast

from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph

from clai.skills import SkillMiddleware, load_skills
from clai.tools import make_run_shell_command

SYSTEM_PROMPT = """You are clai, a command-line assistant that runs shell commands \
with the run_shell_command tool.
Use commands only to get facts about this machine, its files or its repositories.
For general knowledge questions, answer directly without running commands.
Work step by step: run a command, look at its output, then decide the next command.
Never guess about something you can check: if you need a file's contents, read it first.
Never ask the user to run commands; run them yourself.
When you have verified the facts, answer concisely."""
RECURSION_LIMIT = 51
# One conversation per run: every request continues the same thread.
CONFIG = RunnableConfig(
    recursion_limit=RECURSION_LIMIT, configurable={"thread_id": "1"}
)

# stream_mode="messages" yields (message chunk, metadata) pairs,
# but LangGraph's type hints don't say so.
MessageStream = Iterator[tuple[BaseMessage, dict[str, Any]]]


def make_agent(
    model: str | BaseChatModel, confirm: Callable[[str], bool]
) -> CompiledStateGraph:
    """Create an agent that can run shell commands.

    `model` is a "provider:model" name, or a chat model object (tests pass a fake).
    Skills come from ~/.clai/skills/; with none, the agent gets no load_skill tool.
    """
    skills = load_skills()
    return create_agent(
        model,
        tools=[make_run_shell_command(confirm)],
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
        middleware=[SkillMiddleware(skills)] if skills else [],
    )


def ask(agent: CompiledStateGraph, request: str) -> Iterator[str]:
    """Answer a natural-language request, running shell commands when needed."""

    answered = False

    try:
        stream = cast(
            MessageStream,
            agent.stream(
                {"messages": [{"role": "user", "content": request}]},
                CONFIG,
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
    except KeyboardInterrupt:
        _cancel_pending_tool_calls(agent)
        raise

    if not answered:
        yield "The model returned an empty answer. Try again."


def _cancel_pending_tool_calls(agent: CompiledStateGraph) -> None:
    """Answer tool calls cut off by Ctrl-C.

    Providers reject a history where a tool call has no result, so without this
    every later request in the session would fail.
    """
    messages = agent.get_state(CONFIG).values.get("messages", [])
    last = messages[-1] if messages else None
    if isinstance(last, AIMessage) and last.tool_calls:
        cancelled = [
            ToolMessage("Cancelled by the user.", tool_call_id=call["id"])
            for call in last.tool_calls
        ]
        agent.update_state(CONFIG, {"messages": cancelled}, as_node="tools")
