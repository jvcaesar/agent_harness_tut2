# Implementation Plan for agent_harness-tut2

> **Merged** from `PLAN.md` + `Plan-laguna.md` on 2026-08-21. The markdown skill layer and
> packaging phases (previously deferred) are now in scope, per decision.

**Target:** take the current stub scaffold and turn it into a working, testable,
offline-demonstrable, installable minimal agent harness in Python — following the tutorial
*"What is an Agent Harness? And how to build a great one!"*
(<https://www.youtube.com/watch?v=nWzXyjXCoCE>).

**Date:** 2026-08-21 · **Python:** 3.13.1
**Current state:** a 9-component scaffold of stubs with several import-time and logic bugs.
**Goal:** a fully importable, tested, offline-demonstrable agent harness shipped as a small
installable package.

---

## 1. What this project is

An agent harness is the plumbing between an LLM and the world. It provides:

1. A reliable `decide → dispatch → feedback` loop (the only component that talks to the model).
2. Context management (compaction when the message history grows too long).
3. A tool registry (`name → permission → handler`) that emits machine-readable descriptors.
4. Five built-in primitives: `read_file`, `write_file`, `edit_file`, `bash`, `grep`.
5. JSONL session persistence (append-only, replayable).
6. System prompt assembly (static scaffold + discovered instruction files).
7. Pre/post hooks (allow/deny short-circuit, post-dispatch audit/logging).
8. A three-tier permission model (`read` < `workspace` < `full`) with bash command classification.
9. Sub-agent archetypes (`explore`, `general`, `verify`).
10. A markdown-driven **skill layer** (tools composed from `.md` skill definitions).
11. Packaging (`requirements.txt`, `pyproject.toml`) so it installs and runs pytest from root.

The harness is split into modules under `harness/`, plus a `demo/` target project, a `tests/`
suite, and packaging metadata.

---

## 2. Current state — issues found

### 2.1 Import-time crashes

| File | Line | Bug | Fix |
|------|------|-----|-----|
| `builtins.py` | 4 | `from zipfile import Path` | → `from pathlib import Path` |
| `context.py` | 5 | `from attr import dataclass` (3rd-party) | → `from dataclasses import dataclass` |
| `persistence.py` | 7 | `from streamlit import json` (web framework) | → `import json` |
| `subagents.py` | — | `SubAgentSpec` used but undefined; `Permission.READONLY` wrong name; `Permission` not imported | Define `SubAgentSpec`; fix to `Permission.READ_ONLY`; add import |
| `tools.py` | 5 | `from attr import dataclass` | → `from dataclasses import dataclass` |

### 2.2 Missing implementations

| File | Gap |
|------|-----|
| `context.py` | `_summarize()` is called (line 32) but never defined. |
| `loop.py` | `run()` is a bare function with `self` but no class. References `self.context`, `self.model`, `self.tools`, `self._dispatch_tool`, `self.max_iterations` — none exist. |
| `prompt.py` | `STATIC_SCAFFOLD`, `INSTRUCTION_FILES`, `_walk_ancestors()` all undefined. |
| `subagents.py` | `SubAgentRegistry` has only `PRESETS`; no `__init__`, no `get_spec()/spawn()` methods. |
| `tools.py` | Skill layer (markdown-based tool composition) described in comments but not implemented. |

### 2.3 Logic bugs

| File | Issue |
|------|-------|
| `permissions.py` | `can_dispatch` uses `>` instead of `>=`. An agent with `WORKSPACE` permission cannot dispatch a `WORKSPACE`-level tool (2 > 2 = False). Should be `>=`. |
| `permissions.py` | `_READ_CMDS` and `_DANGER_CMDS` contain `...` (Ellipsis) placeholder instead of real commands. |
| `tools.py` | `descriptors()` returns `{"name", "permission", "description"}` — may need `parameters` schema for model function-calling. (Noted; adapt in `_dispatch_tool`.) |

### 2.4 Missing files

| Expected (per README) | Status |
|-----------------------|--------|
| `harness/__init__.py` | ❌ Missing |
| `harness/model.py` | ❌ Missing (optional LLM client wrapper) |
| `demo/main.py` | ❌ Missing (exists only as empty `demo/stub.py`) |
| `demo/test_main.py` | ❌ Missing |
| `demo/agent.md` | ❌ Missing |
| `demo/claude.md` | ❌ Missing |
| `demo/run_demo.py` | ❌ Missing |
| `tests/test_harness.py` | ❌ Missing (exists only as empty `tests/stub.py`) |

### 2.5 Missing project config

- No `requirements.txt`
- No `pyproject.toml` or `setup.py`
- No `conftest.py`

### 2.6 Read-only verification

Only `hooks.py` has a compiled `.pyc` in `__pycache__/` — confirming it is the only stub that
imports without error today. Every other module fails at import time due to the bugs above.

---
## 3. Key design decisions & assumptions

1. **Keep the flat layout.** The package stays at `harness/`, with `demo/` (target project the
   agent edits) and `tests/` at the repo root. Do **not** create the `build/` wrapper from the
   original README diagram (avoids import-path churn); update the README's structure diagram
   instead.
2. **Standard library only for the harness runtime** (`dataclasses`, `pathlib`, `json`,
   `shlex`, `subprocess`, `typing`, `unittest`). Fix the bogus imports (`from zipfile import
   Path`, `from streamlit import json`, `from attr import dataclass`) introduced in the stubs.
   Dev/optional dependencies are pinned in Phase 5 (`pytest`, optional `openai`).
3. **Tests use `unittest`** (stdlib) so the core suite needs no third-party runner; pytest is
   optional (Phase 5) and runs the same tests via a `conftest.py` path shim.
4. **Tool handler contract:** every registered handler is `Callable[[dict], str]` — it receives
   a single dict of arguments. The built-in primitives (`read_file`, etc.) are wrapped by small
   adapter lambdas at registration time.
5. **Model contract:** a model is any callable `model(system_prompt, messages, tool_descriptors)
   -> dict` returning `{"stop_reason": "end_turn"|"tool_call", "text": str, "tool_call":
   {"name": str, "arguments": dict}}`. Provide an offline `DummyModel` (deterministic, scripted)
   so tests and the demo run without API keys, plus an optional OpenAI-compatible client
   (activates only when `openai` is installed and `OPENAI_API_KEY` is set). **Model integration
   is deferred** — tests never hit a live API.
6. **Permissions:** permission is the *session's* current tier (`read` < `workspace` < `full`).
   A tool call is allowed when `RANK[current] >= RANK[required]`. **Fix** the stub's strict `>`
   (equal rank would deny a permitted call). Bash is classified dynamically: read-only commands
   -> `read`, destructive/system commands -> `full`, everything else (including `python`) ->
   `workspace` so the demo can run `python -m unittest`.
7. **`_summarize` heuristic.** Model-based summarization is a `# TODO` drop-in later; Phase 1
   ships a heuristic (concatenate older messages, prepend a summary header, truncate to budget).
8. **Descriptor format.** Model function-calling typically expects `{"type": "function",
   "function": {"name", "description", "parameters"}}`. `Harness._dispatch_tool` adapts the
   registry's simplified shape; a format change is flagged, not blocking.
9. **Skip/hand-wave safety:** implement the sandbox as a thin path guard where cheap, but keep
   the demo offline and harmless. Do not add a full OS isolation layer.

## 4. Target layout (after implementation)

```text
<repo root>/
    README.md              # updated with final structure + status
    PLAN.md                # this document (merged from PLAN.md + Plan-laguna.md)
    requirements.txt       # phase 5: pinned runtime + dev deps
    pyproject.toml         # phase 5: metadata + package discovery (+ conftest.py if needed)
    harness/
        __init__.py        # public exports (Harness, ContextManager, ToolRegistry, etc.)
        loop.py            # 01 Harness + run() goal loop + _dispatch_tool
        context.py         # 02 ContextManager (fix dataclass import, implement _summarize)
        tools.py           # 03 Tool / ToolRegistry + register_core_tools() + skill layer
        subagents.py       # 04 SubAgentSpec + SubAgentRegistry (+ get_spec/spawn)
        builtins.py        # 05 read/write/edit/bash/grep primitives (fix Path import)
        persistence.py     # 06 SessionPersistence (fix json import)
        prompt.py          # 07 STATIC_SCAFFOLD, INSTRUCTION_FILES, _walk_ancestors
        hooks.py           # 08 Hooks + HookContext (complete; verify)
        permissions.py     # 09 Permission tiers, classify_bash, can_dispatch (fill sets, fix >=)
        model.py           # model protocol + DummyModel + optional OpenAI client
    demo/                  # target project the agent edits
        agent.md           # harness-level instructions (picked up by prompt.py)
        claude.md          # picked up by prompt.py (component 07)
        main.py            # contains a deliberately buggy `add()` the agent must fix
        test_main.py       # tests that fail until main.py is fixed
        run_demo.py        # end-to-end runner (works offline via DummyModel)
    tests/
        test_harness.py    # unittest suite validating every component + integration
        .harness/          # generated: session.jsonl event log (gitignored)
```

---
## 5. Work items — 5 phases, 19 steps

Dependency order: Phase 1 → 2 → 3 → 4 → 5. Each step is concrete and checkable.

### Phase 1 · Foundations — fix imports & basic correctness

**Deliverable:** every module in `harness/` imports cleanly.

- **Step 1 — `harness/permissions.py`.** Replace `...` in `_READ_CMDS`/`_DANGER_CMDS` with real
  frozensets (`_READ_CMDS` = ls, cat, head, tail, grep, find, wc, echo, pwd, type, dir, more;
  `_DANGER_CMDS` = rm, del, rmdir, rd, sudo, mv, kill, shutdown, dd, mkfs, chmod, chown, format).
  `classify_bash(cmd)` shlex-splits; empty -> READ_ONLY; base in READ -> READ_ONLY; base in DANGER
  -> FULL; else WORKSPACE (so `python -m unittest` is allowed in the demo). `can_dispatch`
  returns `RANK[current] >= RANK[required]` (fix `>`); unknown levels deny via `.get()`.
- **Step 2 — `harness/builtins.py`.** Fix `from zipfile import Path` -> `from pathlib import
  Path`; keep `read_file`, `edit_file`, `write_file`, `grep`, `bash`. Keep exact signatures
  (`bash(command, timeout=10)`, etc.). `bash` wraps `subprocess.run` with `shell=True`, captures
  stdout/stderr, returns output or error strings.
- **Step 3 — `harness/tools.py`.** Change `from attr import dataclass` -> `dataclasses`. Add
  `ToolRegistry.has(name)` / `names()`. `register_core_tools()` registers the five primitives:
  `read_file`, `grep` -> READ_ONLY; `write_file`, `edit_file` -> WORKSPACE; `bash` -> WORKSPACE
  (re-classified live at dispatch). Wrap handlers to the dict contract
  (`handler=lambda a: read_file(a["path"])`).

### Phase 2 · Support modules

**Deliverable:** context, persistence, prompt, and sub-agent modules import and behave.

- **Step 4 — `harness/hooks.py`.** No logic changes; review only. Ensure `HookDecision`,
  `HookContext`, `Hooks.add_pre/add_post/fire_pre/fire_post` are sound. First `deny`
  short-circuits `fire_pre`.
- **Step 5 — `harness/context.py`.** Fix `attr.dataclass` -> `dataclasses`. Implement
  `ContextManager._summarize(older)` as a heuristic returning
  `{"role": "system", "content": "[summary of N earlier messages omitted]"}` (model-based
  summarization is a later swap-in). `compact_if_needed` passes through below threshold,
  else `[summary] + recent`.
- **Step 6 — `harness/persistence.py`.** Fix `from streamlit import json` -> `import json`.
  `append_event` (ensure dir, append + `flush()`) and `replay` (skip malformed lines) — no
  read/delete/overwrite semantics. `replay` on missing file returns `[]`.
- **Step 7 — `harness/prompt.py`.** Define `STATIC_SCAFFOLD` (multi-line harness rules: "be
  concise", "use the given tools", "end the turn when the goal is met"), `INSTRUCTION_FILES =
  ("AGENTS.md", "CLAUDE.md", "agent.md", "claude.md")`, and `_walk_ancestors(cwd)` yielding
  resolved dir then parents (dedupe). `assemble_system_prompt(cwd, max_per_file=4000,
  max_total=20000)` = scaffold + each instruction file (truncated, bounded).
- **Step 8 — `harness/subagents.py`.** Define `@dataclass SubAgentSpec(name, permission,
  tools: tuple[str, ...], system_prompt)`; import `Permission`; fix `READONLY` ->
  `Permission.READ_ONLY`. `PRESETS` = explore (READ_ONLY, read/grep), general (WORKSPACE, all
  five), verify (WORKSPACE, read/grep/bash). Registry gets `registrations.get(name)`,
  `names()`, `all()`, plus `get_spec(name)` and `spawn(name, goal)` (returns a spec + goal prompt).

### Phase 3 · Core engine + skill layer

**Deliverable:** `from harness import Harness` works with an offline stub model; skills register
and invoke from markdown.

- **Step 9 — `harness/model.py`.** `@runtime_checkable` protocol `Model` with
  `__call__(system_prompt, messages, tools) -> dict`; helpers `end_turn(text)` / `tool_call(name,
  arguments)`; `DummyModel` (scripted via a `policy(response, messages)` callable) for tests +
  offline demo; optional `OpenAIModel` (activates only if `openai` installed and `OPENAI_API_KEY`
  set) converting messages, appending descriptors, and mapping output to `{"stop_reason", "text",
  "tool_call"}`.
- **Step 10 — `harness/loop.py` + `Harness`.** `class Harness(model, cwd=None, max_iterations=10,
  context=None, tools=None, hooks=None, persistence=None, permission=Permission.WORKSPACE)`.
  Defaults build `ContextManager()`, `register_core_tools(ToolRegistry())`, `Hooks()`,
  `SessionPersistence(cwd/.harness/session.jsonl)`. `run(goal)` — assemble prompt, seed goal,
  iterate up to `max_iterations`, compact, call model, return on `end_turn`, else dispatch and
  append `tool_result`; timeout message when exhausted. `_dispatch_tool(tool_call)` — resolve tool
  (unknown -> error string), allow/deny via `can_dispatch`, wrap `tool.handler(arguments)` in
  try/except, run post-hooks, persist a tool_call event, return output as string.
- **Step 11 — `harness/__init__.py`.** Export `Harness`, `ContextManager`, `Tool`,
  `ToolRegistry`, `register_core_tools`, `Hooks`, `HookContext`, `Permission`, `classify_bash`,
  `can_dispatch`, `SessionPersistence`, `assemble_system_prompt`, `SubAgentRegistry`,
  `SubAgentSpec`, `DummyModel`, `Model`, `__version__ = "0.1.0"`. Enables `import harness`.
- **Step 12 — Skill layer in `harness/tools.py` (markdown-composed tools).** Add `Skill`
  dataclass and `register_skill(name, md_path, ...)`; a skill reads its `.md` definition at
  invocation time and composes existing primitives into a new callable. Expose skills via
  `descriptors()` / a dedicated `skill_descriptors()` so the model sees them as tools.

---
### Phase 4 · Demo, hardening & tests

**Deliverable:** the end-to-end demo runs offline; the suite covers every component.

- **Step 13 — `demo/` target project.**
  - `demo/agent.md` — instructions to the agent: use read_file/grep to inspect, edit_file/write_file
    to fix; run `python -m unittest -v` in demo/. Do NOT modify `test_main.py`.
  - `demo/claude.md` — short model-behavior file (component 07 pickup).
  - `demo/main.py` — `def add(a, b): return a - b` (bug) plus a docstring describing intended behavior.
  - `demo/test_main.py` — `unittest` with asserts (`add(2, 3) == 5`, `add(-1, 1) == 0`).
  - `demo/run_demo.py` — builds a `Harness` with `cwd=demo/`, `DummyModel` by default
    (deterministic offline demo: read main.py -> edit bug -> run unittest -> end_turn), optionally
    a real model if env var set. Goal: "Fix the bug in demo/main.py so that all tests in
    demo/test_main.py pass." Prints final state and session log entries.
- **Step 14 — Error handling & safety.** `_dispatch_tool` wraps handler exceptions so the loop
  never crashes mid-trajectory. `permissions.can_dispatch` denies unknown levels. Bash is
  classified dynamically; the `Harness` never auto-elevates a FULL-scope command.
- **Step 15 — `tests/test_harness.py` (unittest) + cleanup.** The suite from §6 below; delete
  empty stubs `demo/stub.py` and `tests/stub.py`.

### Phase 5 · Packaging, docs & validate

**Deliverable:** `pip install -e .` works and `pytest` runs from the project root.

- **Step 16 — `requirements.txt`.** Pin runtime deps (stdlib-only harness → empty/`-e .` line) and
  dev deps (`pytest`; optional `openai` behind a comment for live-mode runs).
- **Step 17 — `pyproject.toml` (+ `conftest.py` if needed).** Project metadata + package discovery
  for `harness`. Add a root `conftest.py` when pytest needs the package on `sys.path`
  (`pythonpath = ["."]` via `pytest.ini_options`, or a plain `conftest.py`). `pip install -e .`
  must succeed; `pytest` collects from root.
- **Step 18 — `README.md`.** Replace the "stubs, not runnable" status; update the structure diagram
  to the flat root layout (no `build/`); add quickstart (`python -m unittest discover -s tests -v`,
  `python demo/run_demo.py`, `pip install -e .` / `pytest`).
- **Step 19 — Final validation gate.**

### 5.1 Verification per phase

| Phase | Check |
|-------|-------|
| Phase 1 | Import every `harness` module individually — no ImportError |
| Phase 2 | `from harness import Harness` — instantiate with a stub model |
| Phase 3 | Register a skill with a markdown file; invoke it through the registry |
| Phase 4 | `python -m unittest discover -s tests -v` all green; `python demo/run_demo.py` runs end-to-end |
| Phase 5 | `pip install -e .` succeeds; `pytest` runs from root |

---

## 6. Test plan (`tests/test_harness.py` — one test method each)

| Area | Tests |
|---|---|
| builtins | write->read round trip; edit replaces and raises when pattern missing; grep hit/no-hit |
| tools | register/get/has/descriptors; unknown tool returns None; registered-skills present |
| context | below threshold -> same list; over threshold -> summary + recent only |
| hooks | pre allow/deny + post recorded |
| persistence | append/replay order round trip; replay on missing file -> [] |
| prompt | walks ancestors, includes AGENTS.md/claude.md, caps max_per_file, scaffold present |
| subagents | presets contain explore/general/verify; fields correct (READ_ONLY fix); spawn returns spec+goal |
| model | DummyModel returns end_turn; tool_call dict shape |
| loop e2e | Harness + DummyModel scripted: read main.py -> edit bug -> unittest -> end_turn; assert goal, files modified, events logged |
| loop permissions | session at READ_ONLY denies edit_file -> error string; loop survives |
| bash | `echo hi` returns output; danger classify requires FULL |

---

## 7. Final validation (Step 19 — run at end; all must pass)

```text
python -m unittest discover -s tests -v         # all green
python demo/run_demo.py                          # prints fixed main.py + session events
python -c "import harness; print(harness.__version__)"   # 0.1.0
pip install -e .                                 # package installs
pytest -q                                        # pytest runs from project root
```

---

## 8. Out of scope / future work (do NOT implement now)

- Model-based context summarization (swap into `_summarize` as the drop-in).
- Streaming, retries, rate limiting, prompt caching, token budgets.
- Anthropic/other provider adapters (keep the `Model` protocol; add when needed).
- Sandboxed bash / docker isolation.
- Real LLM API integration in tests (OpenAI client exists, but the suite stays offline).
- Async / non-blocking tool execution, multi-turn state beyond JSONL, web UI / CLI.
- CI pipelines / full release tooling (metadata is minimal — Phase 5 only).

## Document history

- **2026-08-20** — `PLAN.md` (16-step runbook) and `Plan-laguna.md` (audit + 5-phase plan) created
  independently on the same day.
- **2026-08-21** — merged into this single `PLAN.md`. Skill layer (Phase 3, Step 12) and packaging
  (Phase 5, Steps 16–17) are kept **in scope**; `plan.html` regenerated to match (19 steps).