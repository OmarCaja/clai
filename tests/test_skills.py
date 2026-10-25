from pathlib import Path
from typing import Any

from langchain.agents.middleware import ModelRequest, ModelResponse
from langchain_core.language_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, SystemMessage

from clai.skills import Skill, SkillMiddleware, load_skills, make_load_skill

COMMIT = """---
name: commit
description: "Use when the user asks to commit: reviews changes first."
---
Run git status.
"""


def write_skill(directory: Path, name: str, text: str) -> None:
    (directory / name).mkdir()
    (directory / name / "SKILL.md").write_text(text)


def test_loads_valid_skills_and_skips_broken_ones(tmp_path: Path) -> None:
    write_skill(tmp_path, "commit", COMMIT)
    write_skill(tmp_path, "no-frontmatter", "Just text.")
    write_skill(tmp_path, "unclosed", "---\ndescription: x\nbody")
    write_skill(tmp_path, "no-description", "---\nname: x\n---\nbody")

    assert load_skills(tmp_path) == {
        "commit": Skill(
            "Use when the user asks to commit: reviews changes first.",
            "Run git status.",
        )
    }


def test_missing_skills_folder_means_no_skills(tmp_path: Path) -> None:
    assert load_skills(tmp_path / "nope") == {}


def test_load_skill_returns_instructions_or_lists_names() -> None:
    load_skill = make_load_skill({"commit": Skill("desc", "Run git status.")})

    assert "Run git status." in load_skill.invoke({"skill_name": "commit"})
    assert "Available: commit" in load_skill.invoke({"skill_name": "../etc"})


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
