# clai

**Ask your terminal in plain words.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)

`clai` is a command-line assistant powered by an LLM agent. Ask it a question about your machine, your files or your Git repository; it figures out which shell commands to run, runs them (asking you first when a command could change something), reads the output and answers in rendered Markdown.

```console
$ clai "summarize the last 3 commits"
$ git log -3 --oneline (auto-approved)

                         Last 3 Commits
 • 2c707fd Add streaming Markdown rendering and improve CLI input handling
 • ae685e7 Adding CLAUDE.md
 • 8744f79 Adding interactive mode
```

Built with [LangChain](https://python.langchain.com/) `create_agent`, [LangGraph](https://langchain-ai.github.io/langgraph/) and [Rich](https://github.com/Textualize/rich).

## Features

- **Natural-language requests** — "what's using the most space in this folder?", "explain the last commit", "which files mention TODO?"
- **Agentic loop** — the model runs a command, reads its output, and decides the next step until it has verified the answer.
- **Safe by default** — read-only commands run automatically; anything else needs your explicit `y`.
- **Streaming Markdown** — answers appear as they are generated, with headings, lists, tables and highlighted code.
- **Interactive mode** — keep chatting; the agent remembers earlier turns.
- **Any model** — local models through LM Studio (or any OpenAI-compatible server), Google Gemini, or any provider LangChain supports.

## Installation

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/<your-username>/clai.git
cd clai
uv sync
```

To put `clai` on your `PATH` as a global command:

```bash
uv tool install .
```

## Configuration

The model is chosen with `--model`, falling back to the `CLAI_MODEL` environment variable, then to `google_genai:gemini-2.5-flash-lite`. Models use LangChain's `provider:model` format.

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

> `clai` does not load `.env` by itself. Run it with `uv run --env-file .env clai …`, or export the variables in your shell profile.

## Usage

One-shot request:

```bash
uv run --env-file .env clai "how many Python files are in src?"
```

Interactive mode — type `exit` or press Ctrl-D to quit:

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

| Option | Description |
| --- | --- |
| `request` | What you want to know, in plain words. Required unless `-i` is given. |
| `-m`, `--model` | `provider:model` to use. Defaults to `$CLAI_MODEL`. |
| `-i`, `--interactive` | Keep chatting; the agent remembers earlier turns. |
| `-h`, `--help` | Show help and exit. |

## Safety

`clai` runs real shell commands in your current directory, so every command goes through a check first:

- **Auto-approved** — commands made only of read-only programs (`ls`, `pwd`, `cat`, `head`, `tail`, `wc`, `grep`, `find`, `sort`, `echo`, and `git status|log|diff|show`), optionally joined by pipes.
- **Needs your confirmation** — everything else, including command chaining (`;`, `&&`, `||`), redirection (`>`, `>>`), background jobs (`&`), command substitution (`$(…)`, backticks), and options that make a read-only program write or execute (`find -delete`, `find -exec`, `sort -o`, `--output`).

Commands also time out after 30 seconds, get no stdin, and their output is capped at 10,000 characters before it is sent to the model. The agent stops after 21 steps if it hasn't reached an answer.

The allowlist reduces risk; it is not a sandbox. Read every command before you approve it.

## How it works

```
 you ── request ──► cli.py ──► agent.ask() ──► agent.stream()   (InMemorySaver keeps earlier turns)
                                                    │
                     ┌──────────────────────────────┴─────────────────────────────┐
                     │  LangGraph loop, max 21 steps                              │
                     │                                                            │
                     │   model ──── tool call ────► run_shell_command (tools.py)  │
                     │     ▲                               │                      │
                     │     └────── exit code + output ─────┘                      │
                     └───────┬───────────────────────────────┬────────────────────┘
                             │ text chunks                   │ confirm(command), injected by cli.py
                             ▼                               ▼
                render.MarkdownStream               safety.is_read_only?
                (redraws Markdown as it arrives;      ├─ yes → run it, "(auto-approved)"
                 closed before each prompt)           └─ no  → ask the user [y/N]
```

Text chunks and tool calls are interleaved: the model can write a few words, call a command, then keep writing. That is why the Markdown display is closed before each confirmation prompt and a new block starts afterwards.

| Module | Responsibility |
| --- | --- |
| `cli.py` | Argument parsing, interactive loop, confirmation prompts. |
| `agent.py` | Builds the agent with an in-memory checkpointer and streams its answer. |
| `tools.py` | The `run_shell_command` tool: timeout, output cap, exit code. |
| `safety.py` | Decides which commands are read-only and can skip confirmation. |
| `render.py` | Re-renders streamed text as Markdown while it arrives. |

## Development

```bash
uv sync                          # install runtime and dev dependencies
uv run pre-commit install        # run ruff, mypy and pytest on every commit
```

```bash
uv run pytest -q                 # run the tests
uv run pytest tests/test_safety.py -k rm   # run a subset
uv run ruff check --fix          # lint
uv run ruff format               # format
uv run mypy src tests            # type-check
```

## License

[MIT](LICENSE) © 2026 Omar Caja
