"""clai: ask your terminal in plain words.

How a request flows through the package:

    cli -> console.print_answer -> agent.ask -> the LangChain agent
                                                 |- shell: runs commands, asks first
                                                 '- skills: loads instructions

- `cli`: the `clai` command (arguments, one-shot request).
- `chat`: interactive mode with line history.
- `console`: terminal output and the y/N prompt.
- `agent`: builds the agent and gets its answers; no terminal code.
"""
