"""The `load_skill` tool: the model calls it to read a skill's full instructions."""

from langchain.tools import BaseTool, tool

from clai.skills.loader import Skill


def make_load_skill(skills: dict[str, Skill]) -> BaseTool:
    """Build the `load_skill` tool for the skills loaded at startup.

    A `@tool` function only receives what the model sends, so this factory
    captures `skills` in a closure.
    """

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
