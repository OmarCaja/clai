from clai.shell.tool import MAX_OUTPUT_CHARS, TRUNCATED_NOTE
from clai.shell.tool import run_shell_command as run_shell


def test_runs_command() -> None:
    assert run_shell.invoke({"command": "echo hello"}) == "exit code: 0\nhello\n"


def test_reports_failing_command_exit_code() -> None:
    result = run_shell.invoke({"command": "ls /does-not-exist"})

    assert result.startswith("exit code: ")
    assert not result.startswith("exit code: 0")


def test_truncates_long_output() -> None:
    result = run_shell.invoke({"command": "python3 -c \"print('x' * 20000)\""})

    assert result.endswith(TRUNCATED_NOTE)
    assert len(result) == MAX_OUTPUT_CHARS + len(TRUNCATED_NOTE)
