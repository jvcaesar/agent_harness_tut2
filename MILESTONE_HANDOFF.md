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

## Milestone 4: Harness Loop and Tool Dispatch

**Status:** Complete

### Scope

- `harness/loop.py`
  - turned the loose function into a real `Harness` class with a goal-driven `run()` loop
  - integrated context compaction, model calls, iteration limits, and tool-result feedback
- `harness/hooks.py`
  - verified pre/post hook execution and short-circuit deny behavior remains sound
- `harness/tools.py`
  - added core tool registration and registry support for the dispatch runtime
- `harness/__init__.py`
  - exported the `Harness` class as part of the public package API

### Current implementation evidence

- `Harness.run()` now seeds the goal, compacts messages when needed, calls the model, and continues until the model ends the turn or the iteration budget is exhausted.
- `_dispatch_tool()` resolves tools, enforces the permission gate via `can_dispatch()`, runs pre/post hooks, and persists tool-call events to the session JSONL log.
- Added `tests/test_milestone4.py` for the end-to-end dispatch cycle and the denial case.

### Required validation

Executed in the activated virtual environment:

```powershell
python -m pytest tests/test_milestone4.py -q
python -m pytest tests -q
```

**Result:** `2 passed` for the Milestone 4 checks and `10 passed in 0.06s` overall.

## Milestone 5: Markdown Skill Layer

**Status:** Complete

### Scope

- `harness/tools.py`
  - added a minimal `Skill` abstraction for markdown-backed tool composition
  - exposed `register_skill()` and source-backed `invoke()` behavior
  - kept the registry contract consistent with existing tool descriptors

### Current implementation evidence

- The tool registry now supports markdown-based skill registration alongside core built-ins.
- `Skill.invoke()` resolves the markdown file content at runtime and returns the source text for the model/tool chain.
- Added `tests/test_milestone5.py` for skill registration, descriptor exposure, and invocation.

### Required validation

Executed in the activated virtual environment:

```powershell
python -m pytest tests/test_milestone5.py -q
python -m pytest tests -q
```

**Result:** `1 passed` for the Milestone 5 check and `11 passed in 0.06s` overall.

## Next: Milestone 6

Build the demo project and end-to-end validation path.

### Scope

- `demo/agent.md`
  - add the agent instructions that the prompt assembly should discover
- `demo/claude.md`
  - add a short behavior file for the spawnable instruction discovery flow
- `demo/main.py`
  - create the sample bug and the intended behavior contract
- `demo/test_main.py`
  - validate the bug fix with a unittest suite
- `demo/run_demo.py`
  - wire a script that runs the harness against the demo with the offline dummy model

### Suggested first actions

1. Create the demo target files and a deliberate bug in the sample function.
2. Add the corresponding unittests and confirm they fail before the fix.
3. Wire `run_demo.py` to use `Harness` with a `DummyModel`.
4. Run the demo and the relevant tests inside `.venv` before moving to packaging.

### Constraints

- Keep the demo offline and deterministic.
- Do not begin the packaging milestone until the end-to-end demo is validated.
- Preserve the existing harness, tool, permissions, and skill contracts.
