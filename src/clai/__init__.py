"""clai: ask your terminal in plain words.

How a request flows through the package:

    cli -> console.print_answer -> agent.ask -> the LangChain agent
                                                 |- tools.shell: runs commands
                                                 |- approval: asks before risky ones
                                                 '- skills: loads instructions

- `cli`: the `clai` command (arguments, one-shot request).
- `chat`: interactive mode with line history.
- `console`: terminal output and the y/N prompt.
- `render`: Markdown that redraws while it streams.
- `agent`: builds the agent and streams its answers; no terminal code.
"""
