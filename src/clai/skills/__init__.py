"""Skills: reusable instructions the model loads only when a request needs them.

- `loader`: reads `<name>/SKILL.md` files from disk (plain Python, no LangChain).
- `tool`: the `load_skill` tool that hands the model a skill's instructions.
- `middleware`: `SkillMiddleware`, which lists the skills in the system prompt
  and brings the `load_skill` tool with it.
"""
