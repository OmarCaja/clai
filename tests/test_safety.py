import pytest

from clai.safety import is_read_only


@pytest.mark.parametrize(
    "command",
    [
        "ls",
        "ls -la src",
        "pwd",
        "cat README.md",
        "head -n 20 pyproject.toml",
        "wc -l src/clai/agent.py",
        "grep -rn TODO src",
        "find src -name '*.py'",
        "git status",
        "git log -3",
        "git diff HEAD~1",
        "git show HEAD",
        # pipes are fine when every part is read-only
        "git log --oneline | head -n 5",
        "cat README.md|wc -l",
    ],
)
def test_read_only_commands_are_auto_approved(command: str) -> None:
    assert is_read_only(command)


@pytest.mark.parametrize(
    "command",
    [
        # not on the allowlist
        "rm -rf /",
        "sed -i s/a/b/ file.txt",
        "",
        # git subcommands that change things
        "git push",
        "git commit -m wip",
        "git checkout main",
        "git branch new-feature",
        "git",
        # chaining can hide anything after a safe start
        "ls; rm -rf ~",
        "ls && rm x",
        "ls || rm x",
        "sleep 100 &",
        # redirection writes files
        "cat a.txt > b.txt",
        "echo x >> notes.txt",
        # command substitution runs hidden commands
        "echo $(rm x)",
        "echo `rm x`",
        'echo "$(rm x)"',
        'echo "`rm x`"',
        # a pipe into something that is not read-only
        "cat script.sh | sh",
        "find src -name '*.py' | xargs rm",
        # read-only programs with options that write or execute
        "find . -delete",
        "find . -exec rm {} ;",
        "sort -o out.txt in.txt",
        "git diff --output=patch.txt",
        # unparseable input
        "cat 'unterminated",
    ],
)
def test_other_commands_need_confirmation(command: str) -> None:
    assert not is_read_only(command)
