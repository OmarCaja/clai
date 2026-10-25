from collections.abc import Callable
from pathlib import Path
from typing import Any, NamedTuple

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain.tools import BaseTool, tool
from langchain_core.messages import AIMessage, SystemMessage

SKILLS_DIR = Path.home() / ".clai" / "skills"


class Skill(NamedTuple):
    description: str
    instructions: str


def load_skills(directory: Path = SKILLS_DIR) -> dict[str, Skill]:
    """Read every `<name>/SKILL.md` in `directory`, keyed by folder name."""
    skills = {}
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


def make_load_skill(skills: dict[str, Skill]) -> BaseTool:
    """Build the tool that hands the model a skill's full instructions."""

    @tool
    def load_skill(skill_name: str) -> str:
        """Load the full instructions of a skill listed under Available skills.

        Call it before starting a request that one of those skills describes.
        """
        # Look the name up, never turn it into a path: the model could send "../x".
        skill = skills.get(skill_name)
        if skill is None:
            return f"Skill '{skill_name}' not found. Available: {', '.join(skills)}"
        return f"Loaded skill: {skill_name}\n\n{skill.instructions}"

    return load_skill


class SkillMiddleware(AgentMiddleware):
    """Lists the skills in the system prompt and adds the load_skill tool."""

    def __init__(self, skills: dict[str, Skill]) -> None:
        self.tools = [make_load_skill(skills)]
        listing = "\n".join(f"- {name}: {s.description}" for name, s in skills.items())
        self.skills_prompt = (
            f"\n\n## Available skills\n\n{listing}\n\n"
            "When a request matches a skill, call load_skill first and follow it."
        )

    def wrap_model_call(
        self,
        request: ModelRequest[Any],
        handler: Callable[[ModelRequest[Any]], ModelResponse[Any]],
    ) -> ModelResponse[Any] | AIMessage:
        blocks = request.system_message.content_blocks if request.system_message else []
        system = SystemMessage(
            content_blocks=[*blocks, {"type": "text", "text": self.skills_prompt}]
        )
        return handler(request.override(system_message=system))
