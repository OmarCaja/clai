import subprocess

from langchain.tools import tool

MAX_OUTPUT_CHARS = 10_000
TIMEOUT_SECONDS = 30


@tool
def run_shell_command(command: str) -> str:
    """Run a shell command in the user's current directory and return its output."""

    answer = input(f"$ {command}\nRun this command? [y/N] ")

    if answer.strip().lower() != "y":
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
