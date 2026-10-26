"""Find and parse `SKILL.md` files.

A skill is a folder with a `SKILL.md` inside: YAML-like frontmatter with a
`description`, then the instructions in Markdown. The folder name is the skill name.
"""

from pathlib import Path
from typing import NamedTuple

BUILTIN_SKILLS_DIR = Path(__file__).parent / "builtin"
USER_SKILLS_DIR = Path.home() / ".clai" / "skills"


class Skill(NamedTuple):
    """One skill, as the model sees it."""

    description: str
    """Shown in the system prompt, so the model knows when to load the skill."""

    instructions: str
    """The body of `SKILL.md`, returned by the `load_skill` tool."""


def load_skills(*directories: Path) -> dict[str, Skill]:
    """Read every `<name>/SKILL.md` in each directory, keyed by folder name.

    A skill in a later directory replaces one with the same name in an earlier one.
    Missing directories and unreadable or invalid files are skipped.
    """
    skills = {}
    for directory in directories:
        for path in sorted(directory.glob("*/SKILL.md")):
            # A broken skill file should not stop the CLI from starting.
            try:
                skill = parse_skill(path.read_text())
            except (OSError, UnicodeDecodeError):
                continue
            if skill:
                skills[path.parent.name] = skill
    return skills


def parse_skill(text: str) -> Skill | None:
    """Split a `SKILL.md` into its frontmatter description and its instructions.

    Returns None if the frontmatter is missing, unclosed or has no description.
    """
    if not text.startswith("---"):
        return None
    frontmatter, closed, body = text.removeprefix("---").partition("\n---")
    if not closed:
        return None
    # ponytail: one `key: value` per line, not full YAML (no multi-line values);
    # switch to PyYAML if skills need richer frontmatter.
    fields = {}
    for line in frontmatter.splitlines():
        key, _, value = line.partition(":")
        fields[key.strip()] = value.strip().strip("\"'")
    description = fields.get("description")
    if not description:
        return None
    return Skill(description, body.strip())
