import readline
from pathlib import Path
from typing import cast

import pytest

from clai import chat
from clai.agent import Agent

NO_AGENT = cast(Agent, None)


def test_chat_saves_requests_but_not_exit(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    history = tmp_path / "history"
    lines = iter(["how many files?", "", "exit"])
    monkeypatch.setattr(chat, "HISTORY_FILE", history)
    monkeypatch.setattr("builtins.input", lambda prompt: next(lines))
    monkeypatch.setattr(chat, "print_answer", lambda agent, request: True)
    readline.clear_history()

    chat.chat(NO_AGENT)

    saved = history.read_text()
    assert "files?" in saved
    assert "exit" not in saved
