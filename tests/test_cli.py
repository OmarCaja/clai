import readline
from collections.abc import Iterator
from importlib.metadata import version
from pathlib import Path
from typing import cast

import pytest
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ValidationError

from clai import cli

NO_AGENT = cast(CompiledStateGraph, cast(object, None))


def test_failed_request_is_reported_in_one_line(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def failing_ask(agent: CompiledStateGraph, request: str) -> Iterator[str]:
        yield "Let me check"
        raise ConnectionError("Connection error.\nLong library details.")

    monkeypatch.setattr(cli, "ask", failing_ask)

    assert not cli.print_answer(NO_AGENT, "hi")
    output = capsys.readouterr().out
    assert "Error: The request failed: Connection error." in output
    assert "Long library details" not in output


def test_ctrl_c_stops_only_the_answer(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def interrupted_ask(agent: CompiledStateGraph, request: str) -> Iterator[str]:
        yield "Let me check"
        raise KeyboardInterrupt

    monkeypatch.setattr(cli, "ask", interrupted_ask)

    assert not cli.print_answer(NO_AGENT, "hi")
    assert "Stopped." in capsys.readouterr().out


def test_summarize_keeps_the_message_of_a_validation_error() -> None:
    class Settings(BaseModel):
        port: int

    with pytest.raises(ValidationError) as caught:
        Settings(port="not a number")  # type: ignore[arg-type]

    assert cli.summarize(caught.value) == caught.value.errors()[0]["msg"]
    assert "\n" not in cli.summarize(caught.value)


def test_version_comes_from_the_package(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["clai", "--version"])

    with pytest.raises(SystemExit):
        cli.main()

    assert capsys.readouterr().out.strip() == f"clai {version('clai')}"


def test_chat_saves_requests_but_not_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    history = tmp_path / "history"
    lines = iter(["how many files?", "", "exit"])
    monkeypatch.setattr(cli, "HISTORY_FILE", history)
    monkeypatch.setattr("builtins.input", lambda prompt: next(lines))
    monkeypatch.setattr(cli, "print_answer", lambda agent, request: True)
    readline.clear_history()

    cli.chat(NO_AGENT)

    saved = history.read_text()
    assert "files?" in saved
    assert "exit" not in saved
