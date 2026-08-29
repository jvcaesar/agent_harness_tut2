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

## Milestone 2: Context Compaction, JSONL Persistence, Prompt Assembly

Implement context compaction, JSONL persistence, and system prompt assembly.

**Status:** Complete

### Scope

- `harness/context.py`
  - finish or refine `_summarize` behavior
  - verify compaction keeps the configured recent messages and produces a summary message
- `harness/persistence.py`
  - verify append-only JSONL writes, flush behavior, and replay
- `harness/prompt.py`
  - added `STATIC_SCAFFOLD`, `INSTRUCTION_FILES`, and the ancestor-walking helper
  - now assembles the static prompt plus discovered instruction files

### Current implementation evidence

- `harness/context.py` already has summary compaction that preserves configured recent messages.
- `harness/persistence.py` already has append-only JSONL writes with replay.
- Added `tests/test_milestone2.py` for context compaction, JSONL append/replay, and instruction-file discovery.
- `harness/prompt.py` and `tests/test_milestone2.py` have no editor diagnostics.

### Required validation

Executed in the activated virtual environment:

```powershell
python -m pytest tests/test_milestone2.py -q
```

**Result:** `3 passed in 0.11s`

## Milestone 3: Offline Model Contract and Public API

**Status:** Complete

### Scope

- `harness/model.py`
  - added a `DummyModel` that follows the harness response-dictionary contract
  - added helper response constructors for end-turn and tool-call responses
- `harness/__init__.py`
  - exposed the intended public API and package version
- `harness/subagents.py`
  - verified the registry methods and the `explore`, `general`, and `verify` presets are compatible with the finalized package API

### Current implementation evidence

- `harness/model.py` now includes a runtime-checkable `Model` protocol, `end_turn()`, `tool_call()`, and `DummyModel` with scripted/policy-based execution.
- `harness/__init__.py` exports the key harness types and sets `__version__ = "0.1.0"`.
- The registry in `harness/subagents.py` already preserves `explore`, `general`, and `verify` with the expected permission levels.
- Added `tests/test_milestone3.py` for package exports, model contract checks, and registry behavior.

### Required validation

Executed in the activated virtual environment:

```powershell
python -c "import harness; print(harness.__version__)"
python -m pytest tests -q
```

**Result:** `0.1.0` and `8 passed in 0.06s`

## Next: Milestone 4

Implement the main harness loop and tool dispatch behavior.

### Scope

- `harness/loop.py`
  - turn the loose function into a real `Harness` class with a goal-driven `run()` loop
  - integrate context compaction, model calls, and iteration limits
- `harness/hooks.py`
  - verify pre/post hook execution and short-circuit deny behavior remains sound
- `harness/tools.py`
  - integrate tool dispatch, permission gating, and descriptor generation into the harness runtime

### Suggested first actions

1. Inspect the current `Harness` loop scaffold and tool dispatch assumptions in `harness/loop.py`.
2. Confirm tool registry and permission gate semantics before implementing the dispatch flow.
3. Add a focused end-to-end loop test that exercises a scripted model and a tool call.
4. Run the targeted test set inside `.venv` before moving to later milestones.

### Constraints

- Keep the changes narrow and consistent with the existing harness contracts.
- Do not begin the skill layer, demo, or packaging milestones until the loop is validated.
- Preserve the Milestone 1 permission and tool metadata contracts and the Milestone 3 model API.
