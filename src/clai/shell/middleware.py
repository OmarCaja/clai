"""Pause the agent before every shell command, so the CLI can approve it.

LangChain's `HumanInTheLoopMiddleware` does the pausing: before the tool runs, it
raises a LangGraph interrupt, which saves the run and returns from `invoke`. The caller
then decides about each command and continues the run with `resume`.

It pauses for read-only commands too, so every decision is made in one place.
Asking from inside the tool instead would prompt from a LangGraph worker thread,
where Ctrl-C cannot stop the prompt.
"""

from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.agents.middleware.human_in_the_loop import (
    Decision,
    HITLRequest,
    HITLResponse,
)
from langgraph.types import Command, Interrupt

from clai.shell.read_only import is_read_only
from clai.shell.tool import run_shell_command


def make_review_middleware() -> HumanInTheLoopMiddleware:
    """Build the middleware that pauses before each shell command."""
    return HumanInTheLoopMiddleware(
        interrupt_on={
            run_shell_command.name: {"allowed_decisions": ["approve", "reject"]}
        },
        # `resume` answers with one ordered list of decisions per pause. Pinned
        # because LangChain plans to make "per_call" the default.
        interrupt_mode="batched",
    )


def resume(
    interrupt: Interrupt,
    confirm: Callable[[str], bool],
    auto_approved: Callable[[str], None],
) -> Command[Any]:
    """Decide about each paused command and build the command to resume.

    Read-only commands are approved without asking; the rest go to `confirm`. The
    middleware pauses once per model reply, with every command in it, and expects
    one decision per command, in the same order.
    """
    request: HITLRequest = interrupt.value
    decisions: list[Decision] = []
    for action in request["action_requests"]:
        command = action["args"]["command"]
        if is_read_only(command):
            auto_approved(command)
            approved = True
        else:
            approved = confirm(command)
        decisions.append({"type": "approve"} if approved else {"type": "reject"})
    answer: HITLResponse = {"decisions": decisions}
    return Command(resume=answer)
