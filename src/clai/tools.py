import subprocess
from collections.abc import Callable

from langchain.tools import BaseTool, tool

MAX_OUTPUT_CHARS = 10_000
TIMEOUT_SECONDS = 30


def make_run_shell_command(confirm: Callable[[str], bool]) -> BaseTool:
    """Build the shell tool. `confirm` decides whether a command may run."""

    @tool
    def run_shell_command(command: str) -> str:
        """Run a shell command in the user's current directory and return its output."""

        if not confirm(command):
            return "The user declined to run this command."

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
                timeout=TIMEOUT_SECONDS,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired:
            return f"Command timed out after {TIMEOUT_SECONDS}s."

        output = f"exit code: {result.returncode}\n{result.stdout}{result.stderr}"
        if len(output) > MAX_OUTPUT_CHARS:
            return output[:MAX_OUTPUT_CHARS] + "\n[output truncated]"
        return output

    return run_shell_command
