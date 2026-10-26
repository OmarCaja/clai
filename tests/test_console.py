from collections.abc import Iterator
from typing import Any, cast

import pytest
from pydantic import BaseModel, ValidationError

from clai import console
from clai.agent import Agent

NO_AGENT = cast(Agent, None)


def test_failed_request_is_reported_in_one_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_ask(agent: Agent, *args: Any) -> Iterator[str]:
        yield "Let me check"
        raise ConnectionError("Connection error.\nLong library details.")

    monkeypatch.setattr(console, "ask", failing_ask)

    assert not console.print_answer(NO_AGENT, "hi")
    output = capsys.readouterr().out
    assert "Error: The request failed: Connection error." in output
    assert "Long library details" not in output


def test_ctrl_c_stops_only_the_answer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def interrupted_ask(agent: Agent, *args: Any) -> Iterator[str]:
        yield "Let me check"
        raise KeyboardInterrupt

    monkeypatch.setattr(console, "ask", interrupted_ask)

    assert not console.print_answer(NO_AGENT, "hi")
    assert "Stopped." in capsys.readouterr().out


def test_summarize_keeps_the_message_of_a_validation_error() -> None:
    class Settings(BaseModel):
        port: int

    with pytest.raises(ValidationError) as caught:
        Settings(port="not a number")  # type: ignore[arg-type]

    assert console.summarize(caught.value) == caught.value.errors()[0]["msg"]
    assert "\n" not in console.summarize(caught.value)
