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
uv run pytest tests/test_read_only.py -k "rm"            # single test / subset
uv run ruff check --fix && uv run ruff format
uv run mypy src tests
uv run pre-commit install                 # hooks run ruff, ruff format, mypy, pytest
uv run pre-commit run --all-files         # run every hook now, without committing
```

Model is `provider:model` (passed straight to `create_agent`), from `--model`, else `CLAI_MODEL`, else `google_genai:gemini-2.5-flash-lite`. See `.env.example` for the vars (local LM Studio via `OPENAI_BASE_URL`, or `GEMINI_API_KEY`). Nothing in the code loads `.env`; export the vars or use `uv run --env-file .env ...`.

## Architecture

Flow: `cli.main` → `agent.make_agent(model)` → `console.print_answer` → `agent.ask(agent, request, confirm, auto_approved)` streams text chunks → `render.MarkdownStream`. Code is grouped by domain into small modules; each module (and package `__init__.py`) starts with a docstring saying what it is for.

- **`cli.py`**: entry point only: `parse_args`, build the agent, one-shot request, then `chat` if `-i`.
- **`chat.py`**: interactive loop and readline history (`HISTORY_FILE`, auto-history off so y/N answers stay out).
- **`console.py`**: everything printed: the shared `console` and `answer` stream, `show_command`, `show_error`, `summarize` (one-line library errors), the two approval callbacks (`confirm` prompts `[y/N]`, `auto_approved` prints `(auto-approved)`; both close the Markdown stream first) and `print_answer`.
- **`render.py`**: `MarkdownStream` re-renders the whole text on each chunk, since Markdown can't render chunk by chunk.
- **`agent.py`**: no terminal code. `make_agent` builds the agent with `run_shell_command`, an `InMemorySaver` checkpointer, the review middleware, and `SkillMiddleware` only when skills exist. `Agent` is the type alias for what `create_agent` returns. `ask` uses a fixed `thread_id` so REPL turns share history; it loops `_run` (one `stream_mode=["messages", "updates"]` pass, yielding `model` text and reporting `auto_approved_commands`) and `_resume_if_paused` (reads `get_state(CONFIG).interrupts`, returns `resume(...)` or None). It handles `GraphRecursionError` (`RECURSION_LIMIT` counts graph steps, 2 per tool call), empty answers, and Ctrl-C (`_cancel_pending_tool_calls`). The `cast` to `Stream` exists because LangGraph's stream typing is loose.
- **`tools/shell.py`**: `run_shell_command` is a plain `@tool` with no approval logic; it runs with `shell=True`, timeout, `stdin=DEVNULL`, prefixes `exit code: N`, and truncates at `MAX_OUTPUT_CHARS`.
- **`approval/`**: which commands may run. `review.py` is the LangChain glue: `make_review_middleware()` builds `HumanInTheLoopMiddleware` on `run_shell_command` with `when=needs_review` (pause unless read-only; must stay side-effect free, it re-runs on resume), `auto_approved_commands` picks read-only commands out of a `model` update, and `resume` turns `confirm` answers into a typed `HITLResponse` inside `Command(resume=...)`. `read_only.py` has no LangChain: `is_read_only` rejects backticks/`$(` on the raw string, tokenizes with `shlex` punctuation mode, allows `|` pipes only, rejects any other operator (`;`, `&&`, redirects, `&`), and requires every pipe segment to be an allowlisted program (git limited to read-only subcommands) without forbidden write/exec options. It is security-sensitive: when changing it, add cases to the parametrized lists in `tests/test_read_only.py` (both allowed and rejected).
- **`skills/`**: `loader.py` (plain Python) reads `<name>/SKILL.md` keyed by folder name, later dirs winning: `make_agent` passes `skills/builtin/` (shipped in the wheel, e.g. `commit`) then `~/.clai/skills/`; frontmatter is parsed line by line (no PyYAML, only `description` is used). `tool.py`: `make_load_skill(skills)` is a closure factory that looks names up, never builds paths from them. `middleware.py`: `SkillMiddleware` appends the name/description list to the system prompt in `wrap_model_call` and brings the `load_skill` tool.
- **Tests** mirror modules, flat in `tests/` (`test_<module>.py`, skills ones as `test_skill_<module>.py`).

## Conventions

- Ruff rules and `mypy --strict` are set in `pyproject.toml`. Google-style docstrings are required in `src` (not in tests; test names say what they check). `except Exception` needs a `# noqa: BLE001` with a comment saying why.
- mypy runs over `src` and `tests`; the package ships `py.typed`. Trust mypy over IDE warnings about `@tool` overloads.
- Commit messages are prefixed `[OC] - `.
