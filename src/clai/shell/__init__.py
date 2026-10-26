"""Shell: the agent runs commands, and the user approves any that could change things.

- `read_only`: the allowlist policy, plain Python with no LangChain, so the
  security-sensitive part is easy to read and test on its own.
- `tool`: the `run_shell_command` tool, with no approval logic of its own.
- `middleware`: plugs that policy into LangChain's `HumanInTheLoopMiddleware`,
  which pauses the agent before a command that needs the user's approval.
"""
