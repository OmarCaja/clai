from collections.abc import Callable, Iterable, Sequence
from pathlib import Path
from typing import Any

from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from clai.agent import CONFIG, Agent, ask, make_agent


class ScriptedModel(GenericFakeChatModel):
    """Replies with scripted messages, one per call. Ignores the tools it gets."""

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "ScriptedModel":
        return self


def scripted_agent(replies: Iterable[AIMessage]) -> Agent:
    return make_agent(ScriptedModel(messages=iter(replies)))


def reply(
    agent: Agent,
    request: str,
    confirm: Callable[[str], bool] = lambda command: True,
    auto_approved: Callable[[str], None] = lambda command: None,
) -> str:
    return ask(agent, request, confirm, auto_approved)


def run_command(command: str, call_id: str = "call-1") -> AIMessage:
    call = {"name": "run_shell_command", "args": {"command": command}, "id": call_id}
    return AIMessage("", tool_calls=[call])


def test_runs_a_command_then_answers() -> None:
    agent = scripted_agent([run_command("echo hi"), AIMessage("It printed hi.")])

    assert reply(agent, "say hi") == "It printed hi."

    tool_result = agent.get_state(CONFIG).values["messages"][-2]
    assert isinstance(tool_result, ToolMessage)
    assert "hi" in tool_result.text


def test_declined_command_does_not_run(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    agent = scripted_agent([run_command(f"touch {marker}"), AIMessage("OK, I won't.")])
    asked: list[str] = []

    def decline(command: str) -> bool:
        asked.append(command)
        return False

    assert reply(agent, "create a marker file", confirm=decline) == "OK, I won't."

    assert asked == [f"touch {marker}"]
    assert not marker.exists()
    tool_result = agent.get_state(CONFIG).values["messages"][-2]
    assert "rejected" in tool_result.text


def test_approved_command_runs(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    agent = scripted_agent([run_command(f"touch {marker}"), AIMessage("Done.")])

    assert reply(agent, "create a marker file") == "Done."

    assert marker.exists()


def test_read_only_command_runs_without_asking() -> None:
    def must_not_ask(command: str) -> bool:
        raise AssertionError(f"asked about {command}")

    agent = scripted_agent([run_command("echo hi"), AIMessage("It printed hi.")])
    shown: list[str] = []

    answer = reply(agent, "say hi", confirm=must_not_ask, auto_approved=shown.append)

    assert answer == "It printed hi."
    assert shown == ["echo hi"]


def test_remembers_earlier_requests() -> None:
    agent = scripted_agent([AIMessage("Hi Omar."), AIMessage("Your name is Omar.")])

    reply(agent, "my name is Omar")
    reply(agent, "what is my name?")

    messages = agent.get_state(CONFIG).values["messages"]
    requests = [m.text for m in messages if isinstance(m, HumanMessage)]
    assert requests == ["my name is Omar", "what is my name?"]
