from pathlib import Path

from clai.skills import BUILTIN_SKILLS_DIR, Skill, load_skills

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


def test_later_directory_replaces_skill_with_same_name(tmp_path: Path) -> None:
    builtin, user = tmp_path / "builtin", tmp_path / "user"
    builtin.mkdir()
    user.mkdir()
    write_skill(builtin, "commit", COMMIT)
    write_skill(user, "commit", "---\ndescription: Mine.\n---\nMy way.")

    assert load_skills(builtin, user) == {"commit": Skill("Mine.", "My way.")}


def test_builtin_skills_parse() -> None:
    assert "commit" in load_skills(BUILTIN_SKILLS_DIR)
