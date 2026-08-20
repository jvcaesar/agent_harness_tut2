# Implementation Plan for agent_harness-tut2

Target: take the current stub scaffold and turn it into a working, testable, offline-demonstratable
minimal agent harness in Python.

## Key design decisions

1. **Keep the flat layout.** The package stays at `harness/`, with `demo/` (target project the agent
   edits) and `tests/` at the repo root. Do **not** create the `build/` wrapper from the original
   README diagram (avoids import-path churn); update the README's structure diagram instead.
2. **Standard library only** for the harness itself (`dataclasses`, `pathlib`, `json`, `shlex`,
   `subprocess`, `typing`, `unittest`). Fix the bogus imports (`from zipfile import Path`,
   `from streamlit import json`, `from attr import dataclass`) introduced in the stubs.
3. **Tests use `unittest`** (stdlib) because `pytest` is not installed in this environment - zero new
   dependencies to run the suite.
4. **Tool handler contract:** every registered handler is `Callable[[dict], str]` - it receives a
   single dict of arguments. The built-in primitives (`read_file`, etc.) are wrapped by small adapter
   lambdas at registration time.
5. **Model contract:** a model is any callable `model(system_prompt, messages, tool_descriptors) ->
   dict` returning `{"stop_reason": "end_turn"|"tool_call", "text": str,
   "tool_call": {"name": str, "arguments": dict}}`. Provide an offline `DummyModel` (deterministic,
   scripted) so tests and the demo run without API keys, plus an optional OpenAI-compatible client.
6. **Permissions:** permission is the *session's* current tier (`read` < `workspace` < `full`).
   A tool call is allowed when `RANK[current] >= RANK[required]`. **Fix** the stub's strict `>`
   (equal rank would deny a permitted call). Bash is classified dynamically: read-only commands ->
   `read`, destructive/system commands -> `full`, everything else (including `python`) -> `workspace`
   so the demo can run `python -m unittest`.
7. **Skip/hand-wave safety:** implement the sandbox as a thin path guard where cheap, but keep the
   demo offline and harmless. Do not add a full OS isolation layer.

## Target layout (after implementation)

```text
<repo root>/
    README.md              # updated with final structure + status
    PLAN.md                # this document
    harness/
        __init__.py        # public exports (Harness, ContextManager, ToolRegistry, etc.)
        loop.py            # 01 Harness + run() goal loop + _dispatch_tool
        context.py         # 02 ContextManager (fix dataclass import, implement _summarize)
        tools.py           # 03 Tool / ToolRegistry + register_core_tools()
        subagents.py       # 04 SubAgentSpec + SubAgentRegistry (fix references)
        builtins.py        # 05 read/write/edit/bash/grep primitives (fix Path import)
        persistence.py     # 06 SessionPersistence (fix json import)
        prompt.py          # 07 STATIC_SCAFFOLD, INSTRUCTION_FILES, _walk_ancestors
        hooks.py           # 08 Hooks + HookContext (complete; verify)
        permissions.py     # 09 Permission tiers, classify_bash, can_dispatch (fill sets, fix >=)
        model.py           # model protocol + DummyModel + OpenAI-compatible client
    demo/                  # target project the agent edits
        agent.md           # harness-level instructions (picked up by prompt.py)
        claude.md          # picked up by prompt.py (component 07)
        main.py            # contains a deliberately buggy `add()` the agent must fix
        test_main.py       # tests that fail until main.py is fixed
        run_demo.py        # end-to-end runner (works offline via DummyModel)
        .harness/          # generated: session.jsonl event log (gitignored)
    tests/
        test_harness.py    # unittest suite validating every component + integration
```
## Work items (implement in this dependency order)

### Step 1 - `harness/permissions.py`
- Replace `...` in `_READ_CMDS`/`_DANGER_CMDS` with real frozensets.
- `_READ_CMDS` = ls, cat, head, tail, grep, find, wc, echo, pwd, type, dir, more.
- `_DANGER_CMDS` = rm, del, rmdir, rd, sudo, mv, kill, shutdown, dd, mkfs, chmod, chown, format.
- `classify_bash(cmd)`: shlex-split; empty -> READ_ONLY; base in READ -> READ_ONLY;
  base in DANGER -> FULL; else WORKSPACE (so `python -m unittest` is allowed in the demo).
- `can_dispatch(required, current)`: return `RANK[current] >= RANK[required]` (fix `>`). Use
  `.get()` with 0 default so unknown levels deny.

### Step 2 - `harness/builtins.py`
- Fix `from zipfile import Path` -> `from pathlib import Path`; keep `read_file`, `edit_file`,
  `write_file`, `grep`, `bash`.
- Keep exact signatures (`bash(command, timeout=10)`, etc.). `bash` wraps `subprocess.run` with
  `shell=True`, captures stdout/stderr, returns output or error message strings.

### Step 3 - `harness/tools.py`
- Change `from attr import dataclass` -> `from dataclasses import dataclass`.
- Add `ToolRegistry.has(name)` and `ToolRegistry.names()`.
- Add `register_core_tools(registry)` that registers the five built-in primitives with proper
  permission levels:
  - `read_file`, `grep` -> READ_ONLY
  - `write_file`, `edit_file` -> WORKSPACE
  - `bash` -> WORKSPACE (dynamic classification at dispatch; see Step 12)
- Wrap handlers to the dict contract, e.g. `handler=lambda a: read_file(a["path"])`.

### Step 4 - `harness/hooks.py`
- No logic changes needed. Review only; ensure `HookDecision`, `HookContext`,
  `Hooks.add_pre/add_post/fire_pre/fire_post` are sound.

### Step 5 - `harness/context.py`
- Change `from attr import dataclass` -> `from dataclasses import dataclass`.
- Implement `ContextManager._summarize(older)` as a heuristic (per the stub comment: in
  production swap for model-based summarization). Return a single
  `{"role": "system", "content": f"[summary of {len(older)} earlier messages omitted]"}` message.
- `compact_if_needed(messages)`: passthrough below `compact_threshold`, else
  `[summary] + recent` - signature already correct.

### Step 6 - `harness/persistence.py`
- Change `from streamlit import json` -> `import json`.
- Keep `append_event` (ensure dir, append + `flush()`) and `replay` (skip malformed lines).
- `replay` on missing file returns `[]` (already). No reading/deleting/overwriting semantics.

### Step 7 - `harness/prompt.py`
- Define module constants:
  - `STATIC_SCAFFOLD` - a multi-line string describing the harness, its rules ("be concise",
    "use the given tools", "when the goal is met, ask the harness to end the turn"), and scope.
  - `INSTRUCTION_FILES = ("AGENTS.md", "CLAUDE.md", "agent.md", "claude.md")` so `demo/` files are
    discovered by component. Order by increasing distance from cwd.
  - `_walk_ancestors(cwd) -> Iterator[Path]` yielding resolved dir then parents (dedupe).
- `assemble_system_prompt(cwd, max_per_file=4000, max_total=20000)` as in stub: static scaffold +
  each instruction file (truncated `max_per_file`, bounded by `max_total`).

### Step 8 - `harness/subagents.py`
- Define `@dataclass SubAgentSpec(name, permission, tools: tuple[str, ...], system_prompt)`.
- Import `Permission` from `harness.permissions` (fix undefined refs).
- Fix preset constant bug: `Permission.READ_ONLY` (not `READONLY`).
- `PRESETS` = explore (READ_ONLY, read/grep), general (WORKSPACE, all five), verify
  (WORKSPACE, read/grep/bash). Add `registrations.get(name)`, `registrations.names()`,
  `registrations.all()`.
### Step 9 - `harness/model.py`
- `@runtime_checkable` protocol `Model` with `__call__(system_prompt, messages, tools) -> dict`.
- Helper `end_turn(text)` / `tool_call(name, arguments)` builders returning conforming dicts.
- `DummyModel` - scripted responses (constructor takes a callable `policy(response, messages)`
  returning the next response dict) used for tests + offline demo.
- `OpenAIModel` (optional, only used if `openai` installed and `OPENAI_API_KEY` set): converts the
  conversation to chat messages, appends the tool descriptors, and maps the returned text into
  `{"stop_reason", "text", "tool_call"}`. Keep thin and safe.

### Step 10 - `harness/loop.py` + `Harness`
- Introduce `class Harness` (the stub references `self.*` that must exist):
  - `__init__(self, model, cwd=None, max_iterations=10, context=None, tools=None, hooks=None,
    persistence=None, permission=Permission.WORKSPACE)`. Defaults: `ContextManager()`,
    `register_core_tools(ToolRegistry())`, `Hooks()`,
    `SessionPersistence(cwd/.harness/session.jsonl)`.
  - `run(goal) -> str`: exactly the stub loop - assemble system prompt, seed messages with goal,
    iterate up to `max_iterations`, compact, call model, return on `end_turn` with text;
    otherwise dispatch `tool_call` and append `tool_result`. Return timeout message when
    iterations are exhausted.
  - `_dispatch_tool(tool_call) -> str`: resolve tool in registry (unknown -> error string);
    allow/deny via `can_dispatch`; call `tool.handler(arguments)` wrapped in try/except; run
    post-hooks; persist a tool_call event; return output as string.

### Step 11 - `harness/__init__.py`
- Export public API: `Harness`, `ContextManager`, `Tool`, `ToolRegistry`, `register_core_tools`,
  `Hooks`, `HookContext`, `Permission`, `classify_bash`, `can_dispatch`, `SessionPersistence`,
  `assemble_system_prompt`, `SubAgentRegistry`, `SubAgentSpec`, `DummyModel`, `Model`,
  `__version__ = "0.1.0"`. Enables `import harness`.

### Step 12 - `demo/` (target project)
- `demo/agent.md` - instructions to the agent: use read_file/grep to inspect, edit_file/write_file
  to fix; run `python -m unittest -v` in demo/. Do NOT modify `test_main.py`.
- `demo/claude.md` - short model-behavior file (component 07 pickup).
- `demo/main.py` - `def add(a, b): return a - b` (bug) plus docstring describing intended behavior.
- `demo/test_main.py` - `unittest` with asserts (`add(2, 3) == 5`, `add(-1, 1) == 0`).
- `demo/run_demo.py` - builds a `Harness` with `cwd=demo/`, `DummyModel` by default (deterministic
  offline demo: read main.py -> edit bug -> run unittest -> end_turn), optionally real model if env
  var set. Goal: "Fix the bug in demo/main.py so that all tests in demo/test_main.py pass.".
  Prints final state and session log entries.

### Step 13 - Error handling & safety
- `_dispatch_tool` wraps handler exceptions so the loop never crashes mid-trajectory.
- `permissions.can_dispatch` denies unknown levels.
- Bash is classified dynamically; the `Harness` never auto-elevates a FULL-scope command.

### Step 14 - `tests/test_harness.py` (unittest)
Table of tests (each a test method):
| Area | Tests |
|---|---|
| builtins | write->read round trip; edit replaces and raises when pattern missing; grep hit/no-hit |
| tools | register/get/has/descriptors; unknown tool returns None |
| context | below threshold -> same list; over threshold -> summary + recent only |
| hooks | pre allow/deny + post recorded |
| persistence | append/replay order round trip; replay on missing file -> [] |
| prompt | walks ancestors, includes AGENTS.md/claude.md, caps max_per_file, scaffold present |
| subagents | presets contain explore/general/verify; fields correct (READ_ONLY fix) |
| model | DummyModel returns end_turn; tool_call dict shape |
| loop e2e | Harness + DummyModel scripted: read main.py -> edit bug -> unittest -> end_turn; assert goal, files modified, events logged |
| loop permissions | session at READ_ONLY denies edit_file -> error string; loop survives |
| bash | `echo hi` returns output; danger classify requires FULL |

### Step 15 - README
- Update the structure diagram to the flat layout (no `build/`).
- Add "Build status: implemented" replacing the "stubs" note; keep the "what the project is
  expected to accomplish" section.
- Document quickstart: run `python -m unittest discover -s tests -v` and `python demo/run_demo.py`.

### Step 16 - Final validation (run at end; all must pass)
```text
python -m unittest discover -s tests -v         # all green
python demo/run_demo.py                          # prints fixed main.py + session events
python -c "import harness; print(harness.__version__)"
```

## Out of scope / future work (do NOT implement now)
- Skills compositing layer (markdown-based skill definitions injected via hooks later).
- Model-based context summarization (swap into `_summarize`).
- Streaming, retries, rate limiting, prompt caching, token budgets.
- Anthropic/other adapters (keep the `Model` protocol; add when needed).
- Sandboxed bash / docker isolation.
- `pyproject.toml`/packaging/CI.