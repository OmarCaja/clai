---
name: commit
description: Use when the user asks to commit, save or check in their current changes in a Git repository. Stages everything, writes a message in the style of the project's previous commits, and commits.
---

# Commit the current changes

Run each command on its own (no `&&` or `;`). Use only the commands listed here, and don't repeat one you already ran.
Never edit files yourself: your job is only to commit what is there.

## 1. Stage everything

1. `git add -A`. This stages every change, including new, renamed and deleted files. `.gitignore` keeps out `.env` and build output.
2. `git status --porcelain`. Stop if nothing follows the `exit code: 0` line: there is nothing to commit.
3. If a listed file looks like a secret or local file (`.env`, keys, credentials, large binaries), unstage it with `git restore --staged <file>` and mention it.

## 2. Read the changes

`git diff --staged -- . ':(exclude)*.lock'`. This shows every staged change, new files included.

## 3. Learn the project's commit style

Run `git log -10 --format=%B` once. Copy from those subjects:

- any prefix or ticket tag (e.g. `[OC] - `, `feat:`, `JIRA-123`)
- language, tense ("Add" or "Added") and capitalisation

If there are no commits, use a short imperative subject.

## 4. Write the message and commit

    [OC] - Add skill support with load_skill tool and middleware

    - Load skills from ~/.clai/skills/<name>/SKILL.md at startup
    - List skill descriptions in the system prompt via SkillMiddleware
    - Raise RECURSION_LIMIT to 51 so longer skills can finish

- **Subject**: one line, at most 72 characters, in the project's style. It says what the change does, not which files it touched. No period at the end.
- **Body**: 2 to 5 bullets starting with `- `, each at most 72 characters. Each bullet is one meaningful change and, when it isn't obvious, why. Skip trivia such as formatting, imports or lock file updates.

Commit with exactly two `-m` flags: the subject in double quotes, then all the bullets in one `$'...'` string with `\n` between them. `$'...'` turns each `\n` into a real newline.

    git commit -m "[OC] - Add skill support" -m $'- Load skills from ~/.clai/skills\n- List skill descriptions in the system prompt'

Never run `git commit` without `-m`: Git would open an editor, which hangs here. Inside the message, never use backticks, `$(`, single quotes (`'`) or backslashes other than `\n`.

## 5. Check and report

A `git commit` whose output starts with anything other than `exit code: 0` FAILED. Never report a commit unless `git log -1 --stat` shows it.

1. If a pre-commit hook only reformatted files ("files were modified by this hook"), run `git add -A` and the same `git commit` once more.
2. If a hook failed for any other reason (tests, type errors, lint), stop and show its output. Don't try to fix it.
3. Run `git log -1 --stat` and finish with the commit hash, the full message and the files committed.

Never push, amend, rebase, reset or use `--no-verify` unless the user asks.
