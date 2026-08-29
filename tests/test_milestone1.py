from harness.context import ContextManager
from harness.permissions import Permission, can_dispatch, classify_bash
from harness.subagents import SubAgentRegistry


def test_permission_and_bash_contract():
    assert can_dispatch(Permission.READ_ONLY, Permission.WORKSPACE) is True
    assert can_dispatch(Permission.WORKSPACE, Permission.READ_ONLY) is False
    assert classify_bash("ls -la") == Permission.READ_ONLY
    assert classify_bash("rm -rf /tmp") == Permission.FULL


def test_context_compaction_and_subagent_registry():
    ctx = ContextManager(compact_threshold=10, keep_recent=3)
    messages = [{"role": "user", "content": f"m{i}"} for i in range(12)]
    compacted = ctx.compact_if_needed(messages)

    assert len(compacted) == 4
    assert compacted[0]["role"] == "system"
    assert compacted[-1]["content"] == "m11"

    registry = SubAgentRegistry()
    assert set(registry.PRESETS) >= {"explore", "general", "verify"}
