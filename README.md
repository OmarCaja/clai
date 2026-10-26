# clai

**Ask your terminal in plain words.**

[![CI](https://github.com/OmarCaja/clai/actions/workflows/ci.yml/badge.svg)](https://github.com/OmarCaja/clai/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)

`clai` is a command-line assistant powered by an LLM agent. Ask it a question about your machine, your files or your Git
repository; it figures out which shell commands to run, runs them (asking you first when a command could change
something), reads the output and answers in rendered Markdown.

```console
$ clai "summarize the last 3 commits"
$ git log -3 --oneline (auto-approved)

                         Last 3 Commits
 • 2c707fd Add streaming Markdown rendering and improve CLI input handling
 • ae685e7 Adding CLAUDE.md
 • 8744f79 Adding interactive mode
```

Built with [LangChain](https://python.langchain.com/)
`create_agent`, [LangGraph](https://langchain-ai.github.io/langgraph/) and [Rich](https://github.com/Textualize/rich).

## Features

- **Natural-language requests** — "what's using the most space in this folder?", "explain the last commit", "which files
  mention TODO?"
- **Agentic loop** — the model runs a command, reads its output, and decides the next step until it has verified the
  answer.
- **Safe by default** — read-only commands run automatically; anything else needs your explicit `y`.
- **Streaming Markdown** — answers appear as they are generated, with headings, lists, tables and highlighted code.
- **Skills** — reusable instructions the agent loads when a request matches: built-in ones (`commit`) plus your own in `~/.clai/skills/`.
- **Interactive mode** — keep chatting; the agent remembers earlier turns.
- **Any model** — local models through LM Studio (or any OpenAI-compatible server), Google Gemini, or any provider
  LangChain supports.

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/OmarCaja/clai.git
cd clai
uv sync
```

### Install as a global command

To run `clai` from any folder, install it as a uv tool (in its own isolated environment):

```bash
uv tool install .
```

This copies the current code, so after pulling changes or editing the source, reinstall it:

```bash
uv tool install --reinstall .
```

If you are developing `clai`, install it in editable mode instead. The tool then runs your working copy, so code changes
apply immediately:

```bash
uv tool install --editable .
```

Editable mode tracks your code, not your dependencies: run `uv tool install --editable --reinstall .` after changing
`pyproject.toml`. It also points at this folder, so moving or deleting the repo breaks the tool.

To see where the tool is installed, or remove it:

```bash
uv tool list --show-paths
uv tool uninstall clai
```

## Configuration

The model is chosen with `--model`, falling back to the `CLAI_MODEL` environment variable, then to
`google_genai:gemini-2.5-flash-lite`. Models use LangChain's `provider:model` format.

Copy the example file and edit it:

```bash
cp .env.example .env
```

### Local model with LM Studio

Start the LM Studio server, load a model with tool-calling support, and set:

```dotenv
CLAI_MODEL=openai:qwen/qwen3-30b-a3b-2507
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
```

Any OpenAI-compatible server (Ollama, vLLM, …) works the same way through `OPENAI_BASE_URL`.

### Google Gemini

Get a key from [Google AI Studio](https://aistudio.google.com/apikey) and set:

```dotenv
CLAI_MODEL=google_genai:gemini-2.5-flash-lite
GEMINI_API_KEY=your-key-here
```

> `clai` does not load `.env` by itself. From the repo, run it with `uv run --env-file .env clai …`. For the global
> command, export the variables in your shell profile (e.g. `~/.zshrc`) instead.

## Usage

One-shot request:

```bash
uv run --env-file .env clai "how many Python files are in src?"
```

Interactive mode — type `exit` or press Ctrl-D to quit. Use ↑/↓ to recall earlier requests, including ones from previous sessions (saved in `~/.clai/.clai_history`). Ctrl-C stops the current answer and returns to the prompt:

```bash
uv run --env-file .env clai -i
```

Start interactive mode with a first request:

```bash
uv run --env-file .env clai -i "what changed in the last commit?"
```

Pick a model for one run:

```bash
uv run --env-file .env clai -m openai:qwen/qwen3-30b-a3b-2507 "list the biggest files here"
```

| Option                | Description                                                           |
|-----------------------|-----------------------------------------------------------------------|
| `request`             | What you want to know, in plain words. Required unless `-i` is given. |
| `-m`, `--model`       | `provider:model` to use. Defaults to `$CLAI_MODEL`.                   |
| `-i`, `--interactive` | Keep chatting; the agent remembers earlier turns.                     |
| `-V`, `--version`     | Show the version and exit.                                            |
| `-h`, `--help`        | Show help and exit.                                                   |

## Skills

A skill saves you from typing the same long instructions every time. clai ships with a `commit` skill
(`src/clai/skills/builtin/`). Add your own, each in its own folder, as `~/.clai/skills/<name>/SKILL.md`: a short
frontmatter `description` saying when to use it, then the instructions. A skill of yours with the same name as a
built-in one replaces it.

```markdown
---
name: commit
description: Use when the user asks to commit their changes. Writes a message in the style of previous commits.
---
1. Run `git add -A`, then `git diff --staged -- . ':(exclude)*.lock'`.
2. Run `git log -10 --format=%B` and copy the style of those messages.
3. Run `git commit -m "<message>"`.
4. Confirm with `git log -1 --stat`.
```

The skill is named after its folder. Only the names and descriptions go into the prompt; when a request matches one
(`clai "commit my changes"`), the model calls `load_skill` to read the full instructions and follows them. Skills are
read when `clai` starts, and the commands they run go through the same safety checks as any other.

## Safety

`clai` runs real shell commands in your current directory, so every command goes through a check first:

- **Auto-approved** — commands made only of read-only programs (`ls`, `pwd`, `cat`, `head`, `tail`, `wc`, `grep`,
  `find`, `sort`, `echo`, and `git status|log|diff|show`), optionally joined by pipes.
- **Needs your confirmation** — everything else, including command chaining (`;`, `&&`, `||`), redirection (`>`, `>>`),
  background jobs (`&`), command substitution (`$(…)`, backticks), and options that make a read-only program write or
  execute (`find -delete`, `find -exec`, `sort -o`, `--output`).

Commands also time out after 30 seconds, get no stdin, and their output is capped at 10,000 characters before it is sent
to the model. Press Ctrl-C to stop an agent that keeps running commands.

The allowlist reduces risk; it is not a sandbox. Read every command before you approve it.

## How it works

```
 you ── request ──► cli.py ──► console.py ──► agent.ask() ──► agent.stream()   (InMemorySaver keeps earlier turns)
                                                    │
                     ┌──────────────────────────────┴─────────────────────────────┐
                     │  LangGraph loop                                            │
                     │                                                            │
                     │   model ── tool call ──► HumanInTheLoopMiddleware          │
                     │     ▲                     │ interrupt ──► ask(): read-only?│
                     │     │                     ├─ yes → auto-approve            │
                     │     │                     └─ no  → y/N                     │
                     │     │                     resume with the decisions        │
                     │     └── exit code + output ── run_shell_command (shell/)   │
                     └───────┬───────────────────────────────┬────────────────────┘
                             │ text chunks                   │ confirm / auto_approved (console.py)
                             ▼                               ▼
                render.MarkdownStream              "(auto-approved)" or [y/N]
                (redraws Markdown as it arrives;
                 closed before each prompt)
```

Text chunks and tool calls are interleaved: the model can write a few words, call a command, then keep writing. That is
why the Markdown display is closed before each confirmation prompt and a new block starts afterwards.

| Module                  | Responsibility                                                           |
|-------------------------|--------------------------------------------------------------------------|
| `cli.py`                | The `clai` command: arguments, one-shot request.                         |
| `chat.py`               | Interactive mode (`-i`) with line history.                               |
| `console.py`            | Terminal output: answers, commands, y/N prompt, errors.                  |
| `render.py`             | Re-renders streamed text as Markdown while it arrives.                   |
| `agent.py`              | Builds the agent (checkpointer, middleware), streams answers.            |
| `shell/read_only.py`    | Decides which commands are read-only and can skip confirmation.          |
| `shell/tool.py`         | The `run_shell_command` tool: timeout, output cap, exit code.            |
| `shell/middleware.py`   | Approval middleware: pause before commands, resume with the decisions.   |
| `skills/loader.py`      | Reads and parses `<name>/SKILL.md` files.                                |
| `skills/tool.py`        | The `load_skill` tool: hands the model a skill's instructions.           |
| `skills/middleware.py`  | `SkillMiddleware`: lists skills in the system prompt, adds `load_skill`. |

## Development

```bash
uv sync                          # install runtime and dev dependencies
uv run pre-commit install        # run ruff, mypy and pytest on every commit
uv run pre-commit run --all-files   # run all those checks now, without committing
```

```bash
uv run pytest -q                 # run the tests
uv run pytest tests/test_shell_read_only.py -k rm   # run a subset
uv run ruff check --fix          # lint
uv run ruff format               # format
uv run mypy src tests            # type-check
```

GitHub Actions runs the same checks (`ruff check`, `ruff format --check`, `mypy`, `pytest`) on every push to `main` and
every pull request; see [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## License

[MIT](LICENSE) © 2026 Omar Caja
