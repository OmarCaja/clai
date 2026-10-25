# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

`clai` is a natural-language CLI assistant ("ask your terminal in plain words") built on LangChain `create_agent` + LangGraph. It is a learning project: changes are built in small, explained steps rather than large drops.

## Commands

Uses `uv` (Python ≥3.12).

```bash
uv sync                                   # install deps incl. dev group
uv run clai "explain the last commit"     # one-shot request
uv run clai -i                            # interactive REPL (remembers earlier turns)
uv run clai -m openai:qwen/qwen3-30b-a3b-2507 "..."   # pick a model
uv run pytest -q                          # all tests
uv run pytest tests/test_safety.py -k "rm"            # single test / subset
uv run ruff check --fix && uv run ruff format
uv run mypy src tests
uv run pre-commit install                 # hooks run ruff, ruff format, mypy, pytest
```

Model is `provider:model` (passed straight to `create_agent`), from `--model`, else `CLAI_MODEL`, else `google_genai:gemini-2.5-flash-lite`. See `.env.example` for the vars (local LM Studio via `OPENAI_BASE_URL`, or `GEMINI_API_KEY`). Nothing in the code loads `.env`; export the vars or use `uv run --env-file .env ...`.

## Architecture

Flow: `cli.py` → `agent.make_agent(model, confirm)` → `agent.ask(agent, request)` streams text chunks → printed.

- **`agent.py`**: `make_agent` builds the agent with one tool and an `InMemorySaver` checkpointer; `ask` uses a fixed `thread_id` so REPL turns share history. `ask` is a generator over `stream_mode="messages"`, yielding only text from the `model` node; it handles `GraphRecursionError` (`RECURSION_LIMIT`) and empty answers. The `cast` to `MessageStream` exists because LangGraph's stream typing is loose.
- **`tools.py`**: `make_run_shell_command(confirm)` is a closure factory so the approval policy is injected (tests pass lambdas). The tool runs with `shell=True`, timeout, `stdin=DEVNULL`, prefixes `exit code: N`, and truncates at `MAX_OUTPUT_CHARS`.
- **`safety.py`**: `is_read_only` decides auto-approval. It rejects backticks/`$(` on the raw string, tokenizes with `shlex` punctuation mode, allows `|` pipes only, rejects any other operator (`;`, `&&`, redirects, `&`), and requires every pipe segment to be an allowlisted program (git limited to read-only subcommands) without forbidden write/exec options. It is security-sensitive: when changing it, add cases to the parametrized lists in `tests/test_safety.py` (both allowed and rejected).
- **`skills.py`**: skills live in `~/.clai/skills/<name>/SKILL.md`, keyed by folder name; frontmatter is parsed line by line (no PyYAML, only `description` is used). `SkillMiddleware` appends the name/description list to the system prompt in `wrap_model_call` and brings the `make_load_skill(skills)` tool (closure factory, looks names up in the dict, never builds paths from them). `make_agent` adds the middleware only when skills exist. `RECURSION_LIMIT` counts graph steps (2 per tool call), so skills with many commands need its headroom.
- **`cli.py`**: `confirm` = auto-approve read-only commands (prints `(auto-approved)`), otherwise `ask_user` prompts `[y/N]`.

## Conventions

- mypy runs over `src` and `tests`; the package ships `py.typed`. Trust mypy over IDE warnings about `@tool` overloads.
- Commit messages are prefixed `[OC] - `.
