from collections.abc import Callable
from typing import Any

from langchain.agents.middleware import AgentMiddleware, ModelRequest, ModelResponse
from langchain_core.messages import AIMessage, SystemMessage

from clai.skills import Skill
from clai.tools.load_skill import make_load_skill


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
