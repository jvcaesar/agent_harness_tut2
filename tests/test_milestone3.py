import harness
from harness.model import DummyModel, end_turn, tool_call
from harness.permissions import Permission
from harness.subagents import SubAgentRegistry


def test_package_exports_and_version():
    assert harness.__version__ == "0.1.0"
    assert hasattr(harness, "DummyModel")
    assert hasattr(harness, "SubAgentRegistry")


def test_dummy_model_default_and_scripted_contract():
    default_model = DummyModel()
    default_response = default_model("system", [{"role": "user", "content": "hello"}], [])

    assert default_response["stop_reason"] == "end_turn"
    assert "text" in default_response

    scripted = DummyModel(
        scripted_responses=[
            tool_call("read_file", {"path": "README.md"}),
            end_turn("done"),
        ]
    )

    first = scripted("system", [], [])
    second = scripted("system", [], [])

    assert first["stop_reason"] == "tool_call"
    assert first["tool_call"]["name"] == "read_file"
    assert first["tool_call"]["arguments"] == {"path": "README.md"}
    assert second == {"stop_reason": "end_turn", "text": "done"}


def test_subagent_presets_and_registry_registration():
    registry = SubAgentRegistry()

    explore = registry.get("explore")
    general = registry.get("general")
    verify = registry.get("verify")

    assert explore is not None and explore.permission == Permission.READ_ONLY
    assert general is not None and general.permission == Permission.WORKSPACE
    assert verify is not None and verify.permission == Permission.WORKSPACE

    custom = type(explore)(
        name="custom",
        permission=Permission.READ_ONLY,
        tools=("read_file",),
        system_prompt="Custom",
    )
    registry.register("custom", custom)

    assert registry.get("custom") == custom
