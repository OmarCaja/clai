from collections.abc import Sequence
from typing import Any

import pytest
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from clai.agent import CONFIG, ask, make_agent


class ScriptedModel(GenericFakeChatModel):
    """Replies with scripted messages, one per call. Ignores the tools it gets."""

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "ScriptedModel":
        return self


def scripted_agent(
    replies: list[AIMessage], confirm: Any = lambda command: True
) -> CompiledStateGraph:
    # disable_streaming: the fake cannot stream a reply with no text (a tool call).
    model = ScriptedModel(messages=iter(replies), disable_streaming=True)
    return make_agent(model, confirm)


def run_command(command: str) -> AIMessage:
    call = {"name": "run_shell_command", "args": {"command": command}, "id": "call-1"}
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
