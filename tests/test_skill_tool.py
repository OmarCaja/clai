from clai.skills.loader import Skill
from clai.skills.tool import make_load_skill


def test_load_skill_returns_instructions_or_lists_names() -> None:
    load_skill = make_load_skill({"commit": Skill("desc", "Run git status.")})

    assert "Run git status." in load_skill.invoke({"skill_name": "commit"})
    assert "Available: commit" in load_skill.invoke({"skill_name": "../etc"})
