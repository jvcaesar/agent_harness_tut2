from harness import Harness
from harness.model import DummyModel, end_turn, tool_call
from harness.permissions import Permission


def test_file_tool_denies_path_outside_workspace(tmp_path):
    outside_file = tmp_path.parent / "outside.txt"
    outside_file.write_text("secret", encoding="utf-8")
    feedback: list[str] = []

    def policy(_, messages, __):
        if len(messages) == 1:
            return tool_call("read_file", {"path": str(outside_file)})
        feedback.append(messages[-1]["content"])
        return end_turn("done")

    model = DummyModel(policy=policy)
    harness = Harness(model=model, cwd=tmp_path)

    harness.run("Read the file")

    assert "Tool denied" in feedback[0]
    assert "outside the workspace" in feedback[0]


def test_bash_requires_full_permission_with_explanation(tmp_path):
    feedback: list[str] = []

    def policy(_, messages, __):
        if len(messages) == 1:
            return tool_call("bash", {"command": "echo hello"})
        feedback.append(messages[-1]["content"])
        return end_turn("done")

    model = DummyModel(policy=policy)
    harness = Harness(model=model, cwd=tmp_path, permission=Permission.WORKSPACE)

    result = harness.run("Run a command")

    assert result == "done"
    assert "requires full permission" in feedback[0]


def test_bash_blocks_recursive_deletion_even_with_full_permission(tmp_path):
    feedback: list[str] = []

    def policy(_, messages, __):
        if len(messages) == 1:
            return tool_call("bash", {"command": "rm -rf ."})
        feedback.append(messages[-1]["content"])
        return end_turn("done")

    model = DummyModel(policy=policy)
    harness = Harness(model=model, cwd=tmp_path, permission=Permission.FULL)

    harness.run("Delete files")

    assert "recursive deletion is not allowed" in feedback[0]