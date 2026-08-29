import harness
from harness import Harness
from harness.model import DummyModel, end_turn, tool_call


def test_package_import_and_version():
    assert hasattr(harness, "Harness")
    assert harness.__version__ == "0.1.0"


def test_harness_end_to_end_with_dummy_model(tmp_path):
    target = tmp_path / "output.txt"
    model = DummyModel(
        scripted_responses=[
            tool_call("write_file", {"path": str(target), "content": "hello from harness"}),
            end_turn("done"),
        ]
    )

    harness_run = Harness(model=model, cwd=tmp_path, max_iterations=3)
    result = harness_run.run("write the output file")

    assert result == "done"
    assert target.read_text(encoding="utf-8") == "hello from harness"
