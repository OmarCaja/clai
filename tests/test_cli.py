from importlib.metadata import version

import pytest

from clai import cli


def test_version_comes_from_the_package(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["clai", "--version"])

    with pytest.raises(SystemExit):
        cli.main()

    assert capsys.readouterr().out.strip() == f"clai {version('clai')}"


def test_a_request_is_required_outside_interactive_mode(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr("sys.argv", ["clai"])

    with pytest.raises(SystemExit):
        cli.parse_args()

    assert "a request is required" in capsys.readouterr().err
