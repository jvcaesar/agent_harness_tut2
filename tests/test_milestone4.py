from pathlib import Path

from harness import Harness
from harness.model import DummyModel, end_turn, tool_call
from harness.permissions import Permission


def test_harness_run_dispatches_tool_and_completes(tmp_path):
    target = tmp_path / "artifact.txt"
    model = DummyModel(
        scripted_responses=[
            tool_call("write_file", {"path": str(target), "content": "hello"}),
            end_turn("done"),
        ]
    )
    harness = Harness(model=model, cwd=tmp_path, max_iterations=3)

    result = harness.run("write data")

    assert result == "done"
    assert target.read_text(encoding="utf-8") == "hello"


def test_harness_permission_gate_blocks_workspace_tool():
    harness = Harness(
        model=DummyModel(scripted_responses=[end_turn("done")]),
        cwd=".",
        permission=Permission.READ_ONLY,
    )

    result = harness._dispatch_tool({
        "name": "write_file",
        "arguments": {"path": "example.txt", "content": "blocked"},
    })

    assert "Permission denied" in result
