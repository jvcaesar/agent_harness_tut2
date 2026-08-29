from harness import Harness
from harness.model import DummyModel, end_turn, tool_call


def test_list_tools_returns_registry_tool_descriptions(tmp_path):
    model = DummyModel(scripted_responses=[tool_call("list_tools", {}), end_turn("done")])
    harness = Harness(model=model, cwd=tmp_path)

    result = harness.run("What tools are available?")

    assert result == "done"
    events = harness.persistence.replay()
    assert "list_tools: List the tools available to the agent." in events[0]["result"]
    assert "read_file: Read a file from disk." in events[0]["result"]


def test_tool_descriptors_include_json_parameter_schema(tmp_path):
    harness = Harness(model=DummyModel(), cwd=tmp_path)

    descriptors = harness.tools.descriptors()

    assert all(tool["input_schema"]["type"] == "object" for tool in descriptors)