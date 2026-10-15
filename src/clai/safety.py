import shlex

READ_ONLY_PROGRAMS = {
    "ls",
    "pwd",
    "cat",
    "head",
    "tail",
    "wc",
    "grep",
    "find",
    "sort",
    "echo",
    "git",
}
READ_ONLY_GIT = {"status", "log", "diff", "show"}
# Options that make an otherwise read-only program write files or run commands.
FORBIDDEN_ARGS = ("-delete", "-exec", "-ok", "-fprint", "-o", "--output")
OPERATOR_CHARS = "();<>|&"


def is_read_only(command: str) -> bool:
    """True if the command can run without asking the user first."""
    # Command substitution: shlex keeps these inside words (e.g. in double
    # quotes), but the shell still runs what's inside.
    if "`" in command or "$(" in command:
        return False
    try:
        lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
        lexer.whitespace_split = True
        tokens = list(lexer)
    except ValueError:
        return False

    segments: list[list[str]] = [[]]
    for token in tokens:
        if token == "|":
            segments.append([])
        elif all(ch in OPERATOR_CHARS for ch in token):
            return False
        else:
            segments[-1].append(token)

    return all(_segment_is_read_only(segment) for segment in segments)


def _segment_is_read_only(segment: list[str]) -> bool:
    if not segment or segment[0] not in READ_ONLY_PROGRAMS:
        return False
    if segment[0] == "git" and (len(segment) < 2 or segment[1] not in READ_ONLY_GIT):
        return False
    return not any(arg.startswith(FORBIDDEN_ARGS) for arg in segment[1:])
