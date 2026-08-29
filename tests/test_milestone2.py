from harness.context import ContextManager
from harness.persistence import SessionPersistence
from harness.prompt import assemble_system_prompt


def test_context_compaction_summarizes_old_messages_and_keeps_recent():
    manager = ContextManager(compact_threshold=4, keep_recent=2)
    messages = [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
        {"role": "user", "content": "third"},
        {"role": "assistant", "content": "fourth"},
    ]

    compacted = manager.compact_if_needed(messages)

    assert compacted[0]["role"] == "system"
    assert "first" in compacted[0]["content"]
    assert compacted[1:] == messages[-2:]


def test_session_persistence_appends_and_replays_events(tmp_path):
    persistence = SessionPersistence(tmp_path / "sessions" / "events.jsonl")
    events = [{"event": "started"}, {"event": "tool", "value": 1}]

    for event in events:
        persistence.append_event(event)

    assert persistence.replay() == events


def test_prompt_uses_ancestor_instruction_files_and_limits_dynamic_text(tmp_path):
    root = tmp_path / "root"
    working_directory = root / "nested" / "workspace"
    working_directory.mkdir(parents=True)
    (root / "AGENTS.md").write_text("root instructions", encoding="utf-8")
    (working_directory / "CLAUDE.md").write_text("local instructions", encoding="utf-8")

    prompt = assemble_system_prompt(working_directory, max_per_file=100, max_total=100)

    assert "root instructions" in prompt
    assert "local instructions" in prompt
