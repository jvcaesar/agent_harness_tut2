# Milestone Handoff

## Milestone 1: Foundation Repair and Import Safety

**Status:** Complete

### Completed work

- Repaired import-time dependencies:
  - `harness/builtins.py`: changed `Path` import from `zipfile` to `pathlib`.
  - `harness/context.py`: changed `dataclass` import from `attr` to `dataclasses`.
  - `harness/persistence.py`: changed JSON import from `streamlit` to the Python standard library.
- Repaired `harness/permissions.py`:
  - replaced placeholder command sets with concrete values
  - classified read-only, workspace, and full-access bash commands
  - corrected the permission gate to allow an equal or higher current permission level
  - invalid permission values deny safely
- Normalized `harness/tools.py`:
  - uses the standard-library dataclass
  - exposes `Tool` metadata: name, permission, handler, and description
  - returns `None` for unknown tool lookups
- Stabilized `harness/subagents.py`:
  - added `SubAgentSpec`
  - imported `Permission`
  - changed invalid `Permission.READONLY` usage to `Permission.READ_ONLY`
  - added registry lookup and registration methods
- Added focused Milestone 1 checks in `tests/test_milestone1.py`.

### Verification

The import smoke test was run successfully by the user in the project virtual environment.

```powershell
cd "c:\MyCodeJunk\LearningAi\AI-agents\agent_harness-tut2"
.\.venv\Scripts\python.exe -c "import importlib; modules = ['harness.permissions', 'harness.builtins', 'harness.tools', 'harness.context', 'harness.persistence', 'harness.subagents']; [importlib.import_module(module) for module in modules]; print('OK')"
```

**Result:** `OK`

## Next: Milestone 2

Implement context compaction, JSONL persistence, and system prompt assembly.

### Scope

- `harness/context.py`
  - finish or refine `_summarize` behavior
  - verify compaction keeps the configured recent messages and produces a summary message
- `harness/persistence.py`
  - verify append-only JSONL writes, flush behavior, and replay
- `harness/prompt.py`
  - implement missing `STATIC_SCAFFOLD`, `INSTRUCTION_FILES`, and ancestor-walking helper
  - assemble a static prompt plus discovered instruction files

### Suggested first actions

1. Inspect the current implementations of the three modules above.
2. Add focused tests for compaction, JSONL append/replay, and instruction-file discovery.
3. Make the smallest implementation changes needed for the tests.
4. Run the targeted tests inside `.venv`.

### Constraints

- Keep changes minimal and consistent with the existing project style.
- Do not start the model, loop, demo, or packaging milestones yet.
- Preserve the Milestone 1 contracts for permissions, tool metadata, and sub-agent presets.
