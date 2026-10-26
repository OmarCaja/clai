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
uv run pytest tests/test_shell_read_only.py -k "rm"            # single test / subset
uv run ruff check --fix && uv run ruff format
uv run mypy src tests
uv run pre-commit install                 # hooks run ruff, ruff format, mypy, pytest
uv run pre-commit run --all-files         # run every hook now, without committing
```

Model is `provider:model` (passed straight to `create_agent`), from `--model`, else `CLAI_MODEL`, else `google_genai:gemini-2.5-flash-lite`. See `.env.example` for the vars (local LM Studio via `OPENAI_BASE_URL`, or `GEMINI_API_KEY`). Nothing in the code loads `.env`; export the vars or use `uv run --env-file .env ...`.

## Architecture

Flow: `cli.main` → `agent.make_agent(model)` → `console.print_answer` → `agent.ask(agent, request, confirm, auto_approved)` returns the final answer, printed as plain text. Code is grouped by domain into small modules; each module (and package `__init__.py`) starts with a docstring saying what it is for.

- **`cli.py`**: entry point only: `parse_args`, build the agent, one-shot request, then `chat` if `-i`.
- **`chat.py`**: interactive loop and readline history (`HISTORY_FILE`, auto-history off so y/N answers stay out).
- **`console.py`**: everything printed: the shared rich `console`, `show_command`, `show_error`, the two approval callbacks (`confirm` prompts `[y/N]`, `auto_approved` prints `(auto-approved)`) and `print_answer`, which prints the answer with plain `print` (no Markdown rendering, kept simple on purpose).
- **`agent.py`**: no terminal code. `make_agent` builds the agent with `run_shell_command`, an `InMemorySaver` checkpointer, the review middleware, and `SkillMiddleware` only when skills exist. `Agent` is the type alias for what `create_agent` returns. `ask` uses a fixed `thread_id` so REPL turns share history; it calls `agent.invoke`, with `version="v2"`, and while `result.interrupts` is non-empty it invokes again with `resume(...)`; the answer is the last message's text (no streaming, kept simple on purpose). It is kept minimal on purpose (learning project): no cap on command rounds (each resume is a fresh invocation, so LangGraph's recursion limit never triggers; Ctrl-C is the limit), no empty-answer message, and no repair of the history after Ctrl-C at a prompt (restart `-i` if later requests fail).
- **`shell/`**: one package per feature, same shape as `skills/` (plain-Python logic, `tool.py`, `middleware.py` for the LangChain glue). `tool.py`: `run_shell_command` is a plain `@tool` with no approval logic; it runs with `shell=True`, timeout, `stdin=DEVNULL`, prefixes `exit code: N`, and truncates at `MAX_OUTPUT_CHARS`. `middleware.py` decides which commands may run: `make_review_middleware()` builds `HumanInTheLoopMiddleware` (`interrupt_mode="batched"` pinned, since `resume` answers with an ordered list) that pauses before every `run_shell_command`, and `resume` decides each paused command (read-only → `auto_approved`, else `confirm`) into a typed `HITLResponse` inside `Command(resume=...)`. Approval stays on the interrupt, not in a `wrap_tool_call`: tools run in LangGraph worker threads, where Ctrl-C cannot stop a y/N prompt. `read_only.py` has no LangChain: `is_read_only` rejects backticks/`$(`/newlines on the raw string, tokenizes with `shlex` punctuation mode, allows `|` pipes only, rejects any other operator (`;`, `&&`, redirects, `&`), and requires every pipe segment to be an allowlisted program (git limited to read-only subcommands) without forbidden write/exec options. It is security-sensitive: when changing it, add cases to the parametrized lists in `tests/test_shell_read_only.py` (both allowed and rejected).
- **`skills/`**: `loader.py` (no LangChain) reads `<name>/SKILL.md` keyed by folder name, later dirs winning: `make_agent` passes `skills/builtin/` (shipped in the wheel, e.g. `commit`) then `~/.clai/skills/`; `python-frontmatter` splits the file and PyYAML parses it (only `description` is used); files with invalid YAML, no frontmatter or a non-text description are skipped. `tool.py`: `make_load_skill(skills)` is a closure factory that looks names up, never builds paths from them. `middleware.py`: `SkillMiddleware` appends the name/description list to the system prompt in `wrap_model_call` and brings the `load_skill` tool.
- **Tests** mirror modules, flat in `tests/` (`test_<module>.py`, package ones as `test_<package>_<module>.py`).

## Conventions

- Ruff rules and `mypy --strict` are set in `pyproject.toml`. Google-style docstrings are required in `src` (not in tests; test names say what they check). `except Exception` needs a `# noqa: BLE001` with a comment saying why.
- mypy runs over `src` and `tests`; the package ships `py.typed`. Trust mypy over IDE warnings about `@tool` overloads.
- Use an existing library over hand-written parsing or logic (e.g. `python-frontmatter` for `SKILL.md`, `HumanInTheLoopMiddleware` for approval). A package the code imports is declared in `pyproject.toml`, even when another dependency already pulls it in.
- Commit messages are prefixed `[OC] - `.
