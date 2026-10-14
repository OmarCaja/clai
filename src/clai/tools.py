import subprocess

from langchain.tools import tool


@tool
def run_shell_command(command: str) -> str:
    """Run a shell command in the user's current directory and return its output."""

    answer = input(f"$ {command}\nRun this command? [y/N] ")

    if answer.strip().lower() != "y":
        return "The user declined to run this command."

    result = subprocess.run(
        command, shell=True, capture_output=True, text=True, check=False
    )

    return result.stdout + result.stderr
