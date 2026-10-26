from pathlib import Path
from typing import NamedTuple

BUILTIN_SKILLS_DIR = Path(__file__).parent / "builtin_skills"
USER_SKILLS_DIR = Path.home() / ".clai" / "skills"


class Skill(NamedTuple):
    description: str
    instructions: str


def load_skills(*directories: Path) -> dict[str, Skill]:
    """Read every `<name>/SKILL.md` in each directory, keyed by folder name.

    A skill in a later directory replaces one with the same name in an earlier one.
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
    """Split a SKILL.md into its frontmatter description and its instructions."""
    if not text.startswith("---"):
        return None
    frontmatter, closed, body = text[3:].partition("\n---")
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
