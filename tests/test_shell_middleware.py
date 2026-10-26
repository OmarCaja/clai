from langgraph.types import Interrupt

from clai.shell.middleware import resume


def test_resume_has_one_decision_per_paused_command_in_order() -> None:
    actions = [{"args": {"command": "rm a"}}, {"args": {"command": "rm b"}}]
    interrupt = Interrupt(value={"action_requests": actions})

    command = resume(interrupt, lambda command: command == "rm b", print)

    assert command.resume == {"decisions": [{"type": "reject"}, {"type": "approve"}]}


def test_resume_approves_read_only_commands_without_asking() -> None:
    def must_not_ask(command: str) -> bool:
        raise AssertionError(f"asked about {command}")

    interrupt = Interrupt(value={"action_requests": [{"args": {"command": "ls"}}]})
    shown: list[str] = []

    command = resume(interrupt, must_not_ask, shown.append)

    assert command.resume == {"decisions": [{"type": "approve"}]}
    assert shown == ["ls"]
