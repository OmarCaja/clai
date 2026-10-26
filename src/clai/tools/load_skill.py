from langchain.tools import BaseTool, tool

from clai.skills import Skill


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
