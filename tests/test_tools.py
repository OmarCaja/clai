from pathlib import Path

from clai.tools import MAX_OUTPUT_CHARS, make_run_shell_command


def test_runs_command_when_confirmed() -> None:
    run_shell = make_run_shell_command(confirm=lambda command: True)

    assert run_shell.invoke({"command": "echo hello"}) == "exit code: 0\nhello\n"


def test_does_not_run_command_when_declined(tmp_path: Path) -> None:
    marker = tmp_path / "marker"
    run_shell = make_run_shell_command(confirm=lambda command: False)

    result = run_shell.invoke({"command": f"touch {marker}"})

    assert "declined" in result
    assert not marker.exists()


def test_reports_failing_command_exit_code() -> None:
    run_shell = make_run_shell_command(confirm=lambda command: True)

    result = run_shell.invoke({"command": "ls /does-not-exist"})

    assert result.startswith("exit code: ")
    assert not result.startswith("exit code: 0")


def test_truncates_long_output() -> None:
    run_shell = make_run_shell_command(confirm=lambda command: True)

    result = run_shell.invoke({"command": "python3 -c \"print('x' * 20000)\""})

    assert result.endswith("\n[output truncated]")
    assert len(result) == MAX_OUTPUT_CHARS + len("\n[output truncated]")
