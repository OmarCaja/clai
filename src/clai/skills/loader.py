"""Find and parse `SKILL.md` files.

A skill is a folder with a `SKILL.md` inside: YAML frontmatter with a
`description`, then the instructions in Markdown. The folder name is the skill name.
`python-frontmatter` splits the file and PyYAML parses the frontmatter.
"""

from pathlib import Path
from typing import NamedTuple

import frontmatter
import yaml

BUILTIN_SKILLS_DIR = Path(__file__).parent / "builtin"
USER_SKILLS_DIR = Path.home() / ".clai" / "skills"


class Skill(NamedTuple):
    """One skill, as the model sees it."""

    description: str
    """Shown in the system prompt, so the model knows when to load the skill."""

    instructions: str
    """The body of `SKILL.md`, returned by the `load_skill` tool."""


def load_skills(*directories: Path) -> dict[str, Skill]:
    """Read every `<name>/SKILL.md` in each directory, keyed by the folder name.

    A skill in a later directory replaces one with the same name in an earlier one.
    Missing directories and unreadable or invalid files are skipped.
    """
    skills = {}
    for directory in directories:
        for path in sorted(directory.glob("*/SKILL.md")):
            # A broken skill file should not stop the CLI from starting.
            try:
                skill = parse_skill(path.read_text())
            except (OSError, UnicodeDecodeError, yaml.YAMLError):
                continue
            if skill:
                skills[path.parent.name] = skill
    return skills


def parse_skill(text: str) -> Skill | None:
    """Split a `SKILL.md` into its frontmatter description and its instructions.

    Returns None if there is no frontmatter, or it has no text `description`.

    Raises:
        yaml.YAMLError: if the frontmatter is not valid YAML.
    """
    post = frontmatter.loads(text)
    description = post.metadata.get("description")
    if not isinstance(description, str) or not description.strip():
        return None
    return Skill(description.strip(), post.content.strip())
