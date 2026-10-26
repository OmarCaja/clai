"""Build the agent and get its answers.

The agent is LangChain's `create_agent` loop (model -> tools -> model ...), which
runs as a LangGraph graph. This module knows nothing about the terminal: the CLI
passes in callbacks for anything that needs the user.
"""

from collections.abc import Callable
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain_core.language_models import BaseChatModel
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from clai.shell.middleware import make_review_middleware, resume
from clai.shell.tool import run_shell_command
from clai.skills.loader import BUILTIN_SKILLS_DIR, USER_SKILLS_DIR, load_skills
from clai.skills.middleware import SkillMiddleware

SYSTEM_PROMPT = """You are clai, a command-line assistant that runs shell commands \
with the run_shell_command tool.
Use commands only to get facts about this machine, its files or its repositories.
For general knowledge questions, answer directly without running commands.
Work step by step: run a command, look at its output, then decide the next command.
Never guess about something you can check: if you need a file's contents, read it first.
Never ask the user to run commands; run them yourself.
When you have verified the facts, answer concisely."""

# One conversation per run: every request continues the same thread.
CONFIG = RunnableConfig(configurable={"thread_id": "1"})

# What `create_agent` returns. Its state types don't matter to clai.
Agent = CompiledStateGraph[Any, Any, Any, Any]


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
) -> str:
    """Answer a natural-language request.

    Args:
        agent: from `make_agent`.
        request: what the user asked.
        confirm: asks the user whether a command that needs review may run.
        auto_approved: told about each read-only command, which runs without asking.
    """
    message = {"messages": [{"role": "user", "content": request}]}
    # version="v2" returns a GraphOutput: state in `.value`, pauses in `.interrupts`.
    result = agent.invoke(message, CONFIG, version="v2")
    # The run pauses before each command; `resume` decides about it and continues.
    while result.interrupts:
        decisions = resume(result.interrupts[0], confirm, auto_approved)
        result = agent.invoke(decisions, CONFIG, version="v2")
    return str(result.value["messages"][-1].text)
