from langchain_core.messages import AIMessage
from langgraph.types import Interrupt

from clai.approval.review import auto_approved_commands, resume


def shell_call(command: str) -> dict[str, object]:
    return {"name": "run_shell_command", "args": {"command": command}, "id": command}


def test_auto_approved_commands_are_only_the_read_only_ones() -> None:
    message = AIMessage("", tool_calls=[shell_call("ls"), shell_call("rm x")])

    assert auto_approved_commands({"model": {"messages": [message]}}) == ["ls"]


def test_auto_approved_commands_ignore_other_nodes() -> None:
    assert auto_approved_commands({"tools": {"messages": []}}) == []


def test_resume_has_one_decision_per_paused_command_in_order() -> None:
    actions = [{"args": {"command": "rm a"}}, {"args": {"command": "rm b"}}]
    interrupt = Interrupt(value={"action_requests": actions})

    command = resume(interrupt, confirm=lambda command: command == "rm b")

    assert command.resume == {"decisions": [{"type": "reject"}, {"type": "approve"}]}
