"""The `run_shell_command` tool: how the agent looks at this machine."""

import subprocess

from langchain.tools import tool

MAX_OUTPUT_CHARS = 10_000
TIMEOUT_SECONDS = 30
TRUNCATED_NOTE = "\n[output truncated]"


@tool
def run_shell_command(command: str) -> str:
    """Run a shell command in the user's current directory and return its output."""
    # This docstring is the tool description the model reads. Approval happens
    # before the tool runs, in the agent's review middleware (clai.approval.review).
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
            # A command waiting for input would hang: nobody can type into it.
            stdin=subprocess.DEVNULL,
        )
    except subprocess.TimeoutExpired:
        return f"Command timed out after {TIMEOUT_SECONDS}s."

    # The exit code tells the model whether the command worked, even with no output.
    output = f"exit code: {result.returncode}\n{result.stdout}{result.stderr}"
    if len(output) > MAX_OUTPUT_CHARS:
        return output[:MAX_OUTPUT_CHARS] + TRUNCATED_NOTE
    return output
