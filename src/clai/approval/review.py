"""Pause the agent before a command that needs the user's approval.

LangChain's `HumanInTheLoopMiddleware` does the pausing: before a gated tool call
runs, it raises a LangGraph interrupt, which saves the run and ends the stream.
The caller then asks the user and continues the run with `resume`.
"""

from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.agents.middleware.human_in_the_loop import (
    Decision,
    HITLRequest,
    HITLResponse,
)
from langchain.agents.middleware.types import ToolCallRequest
from langchain_core.messages import AIMessage
from langgraph.types import Command, Interrupt

from clai.approval.read_only import is_read_only
from clai.tools.shell import run_shell_command


def needs_review(request: ToolCallRequest) -> bool:
    """Whether to pause for the user: every command that is not read-only.

    The middleware calls this again when the run resumes, so it must have no side
    effects and give the same answer for the same command.
    """
    return not is_read_only(request.tool_call["args"]["command"])


def make_review_middleware() -> HumanInTheLoopMiddleware:
    """Build the middleware that pauses before shell commands that need review."""
    return HumanInTheLoopMiddleware(
        interrupt_on={
            run_shell_command.name: {
                "allowed_decisions": ["approve", "reject"],
                "when": needs_review,
            }
        }
    )


def auto_approved_commands(update: dict[str, Any]) -> list[str]:
    """Read-only commands the model just asked for, from a `"model"` node update.

    These never pause the run, so this is the only way the CLI learns about them.
    `update` is one item of `agent.stream(..., stream_mode="updates")`: it maps the
    node that just ran to the state changes it made.
    """
    messages = (update.get("model") or {}).get("messages", [])
    return [
        call["args"]["command"]
        for message in messages
        if isinstance(message, AIMessage)
        for call in message.tool_calls
        if call["name"] == run_shell_command.name
        and is_read_only(call["args"]["command"])
    ]


def resume(interrupt: Interrupt, confirm: Callable[[str], bool]) -> Command[Any]:
    """Ask the user about each paused command and build the command to resume.

    The middleware pauses once per model reply, with every command in it that
    needs review, and expects one decision per command, in the same order.
    """
    request: HITLRequest = interrupt.value
    decisions: list[Decision] = []
    for action in request["action_requests"]:
        approved = confirm(action["args"]["command"])
        decisions.append({"type": "approve"} if approved else {"type": "reject"})
    answer: HITLResponse = {"decisions": decisions}
    return Command(resume=answer)
