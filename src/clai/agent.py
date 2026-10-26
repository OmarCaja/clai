"""Build the agent and stream its answers.

The agent is LangChain's `create_agent` loop (model -> tools -> model ...), which
runs as a LangGraph graph. This module knows nothing about the terminal: the CLI
passes in callbacks for anything that needs the user.
"""

from collections.abc import Callable, Iterator
from typing import Any, cast

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.errors import GraphRecursionError
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command

from clai.approval.review import (
    auto_approved_commands,
    make_review_middleware,
    resume,
)
from clai.skills.loader import BUILTIN_SKILLS_DIR, USER_SKILLS_DIR, load_skills
from clai.skills.middleware import SkillMiddleware
from clai.tools.shell import run_shell_command

SYSTEM_PROMPT = """You are clai, a command-line assistant that runs shell commands \
with the run_shell_command tool.
Use commands only to get facts about this machine, its files or its repositories.
For general knowledge questions, answer directly without running commands.
Work step by step: run a command, look at its output, then decide the next command.
Never guess about something you can check: if you need a file's contents, read it first.
Never ask the user to run commands; run them yourself.
When you have verified the facts, answer concisely."""

# LangGraph counts graph steps, not commands: each tool call takes two (model +
# tools), so this allows about 25 commands per request.
RECURSION_LIMIT = 51
# One conversation per run: every request continues the same thread.
CONFIG = RunnableConfig(
    recursion_limit=RECURSION_LIMIT, configurable={"thread_id": "1"}
)

# What `create_agent` returns. Its state types don't matter to clai.
Agent = CompiledStateGraph[Any, Any, Any, Any]
# What the agent receives: a new request, or a Command resuming a paused run.
AgentInput = dict[str, Any] | Command[Any]
# `stream_mode=["messages", "updates"]` yields (mode, data) pairs: for "messages",
# data is a (message chunk, metadata) pair; for "updates", a dict from the node that
# just ran to its output. LangGraph's type hints don't say so.
Stream = Iterator[tuple[str, Any]]


def make_agent(model: str | BaseChatModel) -> Agent:
    """Create an agent that can run shell commands.

    Args:
        model: a "provider:model" name, or a chat model object (tests pass a fake).

    Skills are the built-in ones plus ~/.clai/skills/, where a skill with the same
    name replaces the built-in one. With none, the agent gets no `load_skill` tool.
    """
    middleware: list[AgentMiddleware] = [make_review_middleware()]
    if skills := load_skills(BUILTIN_SKILLS_DIR, USER_SKILLS_DIR):
        middleware.append(SkillMiddleware(skills))
    return create_agent(
        model,
        tools=[run_shell_command],
        system_prompt=SYSTEM_PROMPT,
        # Keeps the conversation between requests, and lets a run pause for review.
        checkpointer=InMemorySaver(),
        middleware=middleware,
    )


def ask(
    agent: Agent,
    request: str,
    confirm: Callable[[str], bool],
    auto_approved: Callable[[str], None],
) -> Iterator[str]:
    """Answer a natural-language request, yielding the answer's text as it arrives.

    Args:
        agent: from `make_agent`.
        request: what the user asked.
        confirm: asks the user whether a command that needs review may run.
        auto_approved: told about each read-only command, which runs without asking.
    """
    answered = False
    next_input: AgentInput | None = {"messages": [{"role": "user", "content": request}]}
    try:
        # Each pass runs until the answer is done or a command needs review.
        while next_input is not None:
            for text in _run(agent, next_input, auto_approved):
                answered = True
                yield text
            next_input = _resume_if_paused(agent, confirm)
    except GraphRecursionError:
        yield f"Stopped after {RECURSION_LIMIT} steps without a final answer."
        return
    except KeyboardInterrupt:
        _cancel_pending_tool_calls(agent)
        raise

    if not answered:
        yield "The model returned an empty answer. Try again."


def _run(
    agent: Agent, agent_input: AgentInput, auto_approved: Callable[[str], None]
) -> Iterator[str]:
    """Stream one run of the agent, yielding the text the model writes."""
    stream = cast(
        Stream, agent.stream(agent_input, CONFIG, stream_mode=["messages", "updates"])
    )
    for mode, data in stream:
        if mode == "updates":
            for command in auto_approved_commands(data):
                auto_approved(command)
        else:
            token, metadata = data
            # Tool results stream too; only the model's text is the answer.
            if metadata["langgraph_node"] == "model" and token.text:
                yield token.text


def _resume_if_paused(
    agent: Agent, confirm: Callable[[str], bool]
) -> Command[Any] | None:
    """After a run ends: the Command to continue it if it paused for review."""
    interrupts = agent.get_state(CONFIG).interrupts
    return resume(interrupts[0], confirm) if interrupts else None


def _cancel_pending_tool_calls(agent: Agent) -> None:
    """Answer the tool calls cut off by Ctrl-C.

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
