from typing import Any

from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, SystemMessage

from clai.skills.loader import Skill
from clai.skills.middleware import SkillMiddleware


def test_middleware_appends_skills_to_system_prompt() -> None:
    middleware = SkillMiddleware({"commit": Skill("Commits changes.", "...")})
    request: ModelRequest[Any] = ModelRequest(
        model=GenericFakeChatModel(messages=iter([])),
        messages=[],
        system_message=SystemMessage("You are clai."),
    )
    seen: list[ModelRequest[Any]] = []

    def handler(req: ModelRequest[Any]) -> ModelResponse[Any]:
        seen.append(req)
        return ModelResponse(result=[AIMessage("ok")])

    middleware.wrap_model_call(request, handler)

    assert seen[0].system_message is not None
    prompt = seen[0].system_message.text
    assert prompt.startswith("You are clai.")
    assert "- commit: Commits changes." in prompt
    assert [t.name for t in middleware.tools] == ["load_skill"]
