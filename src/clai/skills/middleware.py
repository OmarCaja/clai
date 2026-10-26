"""`SkillMiddleware`: tells the model which skills exist and how to load them."""

from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, SystemMessage

from clai.skills.loader import Skill
from clai.skills.tool import make_load_skill


class SkillMiddleware(AgentMiddleware):
    """Lists the skills in the system prompt and adds the `load_skill` tool.

    Only names and descriptions go into the prompt, so it stays small however long
    the instructions are; the model loads the instructions when it needs them.
    """

    def __init__(self, skills: dict[str, Skill]) -> None:
        # `create_agent` collects the tools of every middleware from `self.tools`.
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
        """Append the skills listing to the system prompt before each model call."""
        blocks = request.system_message.content_blocks if request.system_message else []
        system = SystemMessage(
            content_blocks=[*blocks, {"type": "text", "text": self.skills_prompt}]
        )
        return handler(request.override(system_message=system))
