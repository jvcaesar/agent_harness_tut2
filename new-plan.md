# Project Implementation Plan

## 1) Current repo state and findings

This project is not yet a working harness. It has the expected module layout under `harness/`, but several files are still engineering stubs or import-broken.

The concrete findings in the current repo are:

- `harness/builtins.py` imports `Path` from `zipfile` instead of `pathlib`.
- `harness/context.py` imports `dataclass` from `attr` instead of the standard library `dataclasses` module.
- `harness/persistence.py` imports `json` from `streamlit` instead of the Python stdlib.
- `harness/permissions.py` contains placeholder `...` values and uses the wrong comparison when checking permissions.
- `harness/subagents.py` references `SubAgentSpec` and `Permission.READONLY`, but neither is defined consistently with the rest of the package.
- `harness/prompt.py` references missing constants and helper functions.
- `harness/loop.py` is a loose function, not a real `Harness` class, and it references fields that do not exist yet.
- `harness/tools.py` does not yet implement the target registry and skill layer described in the project goals.
- The repo is missing the public package exports, model wrapper, demo project files, and a real test suite.

This means the original concept is still valid, but the codebase is not close enough to the target state to start the demo or packaging work yet. The work should proceed in the order of foundation repair, support-module completion, engine implementation, then demo validation.

## 2) Project objective

Build a minimal but functional Python agent harness that can:

- run a goal-driven `decide -> dispatch -> feedback` loop
- compact context before the message history grows too large
- expose a tool registry with permission gating
- include the five required built-ins: `read_file`, `write_file`, `edit_file`, `bash`, and `grep`
- persist actions in append-only JSONL logs
- assemble a system prompt from instruction files and a static scaffold
- work with a simple offline model for testing and demo execution
- fix a sample project bug and validate that fix with automated tests

## 3) Strategic recommendations

### Recommendation 1: fix the broken foundations first
The repo cannot progress to the core engine until modules import cleanly and permissions are defined correctly. This is the first gate.

### Recommendation 2: keep the implementation in narrow, testable milestones
Do not make a large monolithic pass. Each milestone should be small enough to be executed by a single AI agent session and validated with a concrete command.

### Recommendation 3: keep an offline-first model contract
Use a `DummyModel` for all internal test execution and demonstration. Treat a live model as optional infrastructure, not the first goal.

### Recommendation 4: make progress visible and auditable
Every milestone should have an explicit status, verification command, and blocker note. This helps maintain accountability and avoids “looks done” traps.

## 4) Risk management and mitigation

### Risk: import-time failures block everything else
Mitigation:
- repair wrong imports in the currently broken modules first
- validate `import` behavior before building new logic

### Risk: the project design drifts from the repo state
Mitigation:
- audit the actual files before each milestone
- do not assume the tutorial description is already implemented

### Risk: unsafe tool usage from weak permission logic
Mitigation:
- treat permission checks as a core security boundary
- verify bash classification and allow/deny rules before dispatch work is completed

### Risk: adding the demo before the engine is stable
Mitigation:
- delay all demo work until the harness loop is functioning in a scripted test run

### Risk: vague milestone completion
Mitigation:
- every milestone must include a clear goal, file list, verification step, and completion evidence

## 5) Milestone tracker for implementation

Use these milestone entries as the working execution checklist. Each milestone should be tracked as: `not started`, `in progress`, or `complete`, with an exact verification command recorded.

### Milestone 1 — Foundation repair and import safety
- Goal: make all modules import cleanly and establish the correct permission and tool contracts.
- Files: `harness/permissions.py`, `harness/builtins.py`, `harness/tools.py`, `harness/context.py`, `harness/persistence.py`, `harness/subagents.py`
- Specific tasks:
  - fix broken imports and runtime dependencies
  - replace placeholder permission values
  - correct comparison logic in permission checks
  - ensure tool registry behavior matches the intended API
- Verification:
  - run a Python import smoke test over all harness modules
  - confirm no module raises an import-time exception
- Status: [ ] not started | [ ] in progress | [ ] complete
- Blockers: none / list any issue

### Milestone 2 — Context compaction, JSONL persistence, prompt assembly
- Goal: bring the support modules to a usable state.
- Files: `harness/context.py`, `harness/persistence.py`, `harness/prompt.py`
- Specific tasks:
  - implement `_summarize` behavior
  - implement append-only JSONL persistence and replay
  - assemble the system prompt from static scaffold plus instruction files
- Verification:
  - compact a list of messages beyond the threshold and inspect the result shape
  - append and replay a temporary JSONL session file
  - read the assembled prompt and confirm instruction files are included
- Status: [ ] not started | [ ] in progress | [ ] complete
- Blockers: none / list any issue

### Milestone 3 — Model contract and sub-agent registry
- Goal: define a stable offline model interface and the sub-agent presets.
- Files: `harness/subagents.py`, `harness/model.py`, `harness/__init__.py`
- Specific tasks:
  - define `SubAgentSpec` and registry methods
  - implement a `DummyModel` with a simple response contract
  - export the public API from the package
- Verification:
  - successfully import `harness`
  - instantiate the dummy model and inspect the returned dict structure
  - confirm registry contains `explore`, `general`, and `verify`
- Status: [ ] not started | [ ] in progress | [ ] complete
- Blockers: none / list any issue

### Milestone 4 — Main harness engine and tool dispatch
- Goal: implement the loop that decides, dispatches tools, and tracks results.
- Files: `harness/loop.py`, `harness/hooks.py`, `harness/tools.py`
- Specific tasks:
  - create the real `Harness` class
  - implement the `run(goal)` loop
  - implement `_dispatch_tool`
  - integrate permission checks and hook execution
  - persist tool-call activity
- Verification:
  - drive a scripted tool call from a fake model and assert completion
  - confirm denial logic rejects a tool call above the current permission level
- Status: [ ] not started | [ ] in progress | [ ] complete
- Blockers: none / list any issue

### Milestone 5 — Markdown skill layer
- Goal: support higher-level skills composed from markdown definitions.
- Files: `harness/tools.py`
- Specific tasks:
  - add the `Skill` concept
  - register and expose skills through the existing tool registry
  - ensure skill invocation still respects the permission gate
- Verification:
  - register and invoke a skill object through the registry
  - assert the tool descriptor and return value shapes
- Status: [ ] not started | [ ] in progress | [ ] complete
- Blockers: none / list any issue

### Milestone 6 — Demo project and end-to-end validation
- Goal: prove the harness can fix a real bug and validate the result with tests.
- Files: `demo/agent.md`, `demo/claude.md`, `demo/main.py`, `demo/test_main.py`, `demo/run_demo.py`
- Specific tasks:
  - create the demo project files
  - inject a deliberate bug in the sample function
  - ensure the harness can inspect, edit, and validate the fix using tests
- Verification:
  - run the demo end-to-end and confirm the test suite passes
  - confirm a session log is created and persisted
- Status: [ ] not started | [ ] in progress | [ ] complete
- Blockers: none / list any issue

### Milestone 7 — Test coverage, packaging, and final acceptance
- Goal: leave the repo installable, testable, and reviewable.
- Files: `tests/test_harness.py`, `requirements.txt`, `pyproject.toml`, `README.md`
- Specific tasks:
  - write unit tests for the core harness behavior
  - add packaging metadata for installability
  - remove placeholder stub files
  - update project documentation to match actual behavior
- Verification:
  - `python -m unittest discover -s tests -v`
  - `python -c "import harness; print(harness.__version__)"`
  - `pip install -e .`
  - `pytest -q`
- Status: [ ] not started | [ ] in progress | [ ] complete
- Blockers: none / list any issue

## 6) Implementation sequence

1. Milestone 1
2. Milestone 2
3. Milestone 3
4. Milestone 4
5. Milestone 5
6. Milestone 6
7. Milestone 7

The order is intentional. The current repo is not yet structurally stable enough to jump to the demo or live model work.

## 7) Working status template for each AI session

Each implementation pass should follow this format:

- Milestone: <name>
- Objective: <clear one-line outcome>
- Files to change: <list>
- Tasks completed:
  - [ ] task 1
  - [ ] task 2
- Verification command:
  - `<exact command>`
- Result: pass / fail / blocked
- Issues or blockers:
  - <text>
- Next step:
  - <next single action>

This format keeps the session accountable and makes it easy to review progress between agent runs.

## 8) Definition of done

The project is only complete when:

- every harness module imports successfully
- permission checks behave correctly for read, workspace, and full access
- the tool registry and built-ins execute as expected
- the loop completes with a scripted offline model
- session events are logged in append-only JSONL format
- the demo project is fixed and validated by tests
- the repo passes its test suite and can be installed using `pip install -e .`

## 9) Notes for the implementation agent

This plan is based on the current repo state and is intentionally specific to this project. It does not rely on public generic boilerplate. It is designed to be used as a direct execution checklist while also providing a clean progress-tracking mechanism for implementation, verification, and accountability.
