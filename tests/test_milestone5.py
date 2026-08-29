from pathlib import Path

from harness.permissions import Permission
from harness.tools import Skill, ToolRegistry


def test_skill_registry_registers_and_invokes_markdown_skill(tmp_path):
    skill_dir = tmp_path / "skills"
    skill_dir.mkdir()
    skill_path = skill_dir / "summarize.md"
    skill_path.write_text("Summarize the file contents for the model.", encoding="utf-8")

    registry = ToolRegistry()
    registry.register_skill(
        "summarize",
        Permission.READ_ONLY,
        source=str(skill_path),
        description="Summarize a file by reading its markdown definition.",
    )

    skill = registry.get_tool("summarize")
    assert isinstance(skill, Skill)
    assert skill.permission == Permission.READ_ONLY
    assert any(item["name"] == "summarize" for item in registry.descriptors())
    assert "Summarize the file contents" in skill.invoke({})
