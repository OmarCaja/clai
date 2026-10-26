from typing import Any, cast

import pytest

from clai import console
from clai.agent import Agent

NO_AGENT = cast(Agent, None)


def test_failed_request_is_reported_in_one_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_ask(agent: Agent, *args: Any) -> str:
        raise ConnectionError("Connection error.\nLong library details.")

    monkeypatch.setattr(console, "ask", failing_ask)

    assert not console.print_answer(NO_AGENT, "hi")
    output = capsys.readouterr().out
    assert "Error: The request failed: Connection error." in output


def test_ctrl_c_stops_only_the_answer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def interrupted_ask(agent: Agent, *args: Any) -> str:
        raise KeyboardInterrupt

    monkeypatch.setattr(console, "ask", interrupted_ask)

    assert not console.print_answer(NO_AGENT, "hi")
    assert "Stopped." in capsys.readouterr().out
