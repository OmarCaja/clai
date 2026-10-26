"""Approval: which shell commands may run without asking the user.

- `read_only`: the allowlist policy, plain Python with no LangChain, so the
  security-sensitive part is easy to read and test on its own.
- `review`: plugs that policy into LangChain's `HumanInTheLoopMiddleware`, which
  pauses the agent before a command that needs the user's approval.
"""
