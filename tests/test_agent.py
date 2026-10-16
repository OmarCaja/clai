import itertools
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

import pytest
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from clai.agent import CONFIG, RECURSION_LIMIT, ask, make_agent


class ScriptedModel(GenericFakeChatModel):
    """Replies with scripted messages, one per call. Ignores the tools it gets."""

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "ScriptedModel":
        return self


def scripted_agent(
    replies: Iterable[AIMessage], confirm: Any = lambda command: True
) -> CompiledStateGraph:
    # disable_streaming: the fake cannot stream a reply with no text (a tool call).
    model = ScriptedModel(messages=iter(replies), disable_streaming=True)
    return make_agent(model, confirm)


def run_command(command: str, call_id: str = "call-1") -> AIMessage:
    call = {"name": "run_shell_command", "args": {"command": command}, "id": call_id}
    return AIMessage("", tool_calls=[call])


def test_runs_a_command_then_answers() -> None:
    agent = scripted_agent([run_command("echo hi"), AIMessage("It printed hi.")])

    assert "".join(ask(agent, "say hi")) == "It printed hi."

    tool_result = agent.get_state(CONFIG).values["messages"][-2]
    assert isinstance(tool_result, ToolMessage)
    assert "hi" in tool_result.text


def test_ctrl_c_at_a_command_keeps_the_conversation_usable() -> None:
    def press_ctrl_c(_command: str) -> bool:
        raise KeyboardInterrupt

    agent = scripted_agent(
        [run_command("rm notes.txt"), AIMessage("2 + 2 = 4")], confirm=press_ctrl_c
    )

    with pytest.raises(KeyboardInterrupt):
        list(ask(agent, "delete notes.txt"))

    # The cut-off tool call got a result, so the history is valid again...
    last = agent.get_state(CONFIG).values["messages"][-1]
    assert isinstance(last, ToolMessage)
    assert last.tool_call_id == "call-1"
    # ...and the next request works.
    assert "".join(ask(agent, "what is 2 + 2?")) == "2 + 2 = 4"


def test_declined_command_does_not_run(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    agent = scripted_agent(
        [run_command(f"touch {marker}"), AIMessage("OK, I won't.")],
        confirm=lambda command: False,
    )

    assert "".join(ask(agent, "create a marker file")) == "OK, I won't."

    assert not marker.exists()
    tool_result = agent.get_state(CONFIG).values["messages"][-2]
    assert "declined" in tool_result.text


def test_stops_a_model_that_never_answers() -> None:
    # Like a real model, each call gets a new id.
    agent = scripted_agent(
        run_command("echo again", call_id=f"call-{n}") for n in itertools.count()
    )

    answer = "".join(ask(agent, "loop forever"))

    assert answer == f"Stopped after {RECURSION_LIMIT} steps without a final answer."


def test_reports_an_empty_answer() -> None:
    agent = scripted_agent([AIMessage("")])

    assert "".join(ask(agent, "hi")) == "The model returned an empty answer. Try again."


def test_remembers_earlier_requests() -> None:
    agent = scripted_agent([AIMessage("Hi Omar."), AIMessage("Your name is Omar.")])

    list(ask(agent, "my name is Omar"))
    list(ask(agent, "what is my name?"))

    messages = agent.get_state(CONFIG).values["messages"]
    requests = [m.text for m in messages if isinstance(m, HumanMessage)]
    assert requests == ["my name is Omar", "what is my name?"]
