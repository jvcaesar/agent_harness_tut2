# Feature Log

Running log of features added on top of the base harness/agent tutorial. Update this file
whenever a new feature lands; keep entries append-only and dated.

---

## User-named participants (custom user/agent names)

**Implemented:** 2026-08-29
**Status:** Complete
**Files touched:** `agent.py`, `harness/loop.py`, `harness/prompt.py`
**Tests:** `tests/test_interactive_runner.py`, `tests/test_harness.py` (7 passed, no regressions)

### Summary

The interactive CLI now asks for the user's name and a name for the agent at startup.
Both names flow through to:

- `TerminalFormatter` — prompt/response/error labels use the chosen names instead of the
  hardcoded `"You>"` / `"AI>"` / `"AI error:"` strings. Defaults remain `"You"` / `"AI"` when
  left blank, so existing behavior and tests are unchanged.
- `Harness` — accepts `user_name` / `agent_name` constructor args and stores them.
- `assemble_system_prompt` — accepts `user_name` / `agent_name` and, when provided, adds an
  identity line instructing the model to refer to itself by `agent_name` and address the user
  by `user_name` instead of "you"/"AI".

### Rationale

Originated from a note in `Notes.txt`: personalizing the conversation (real names instead of
generic "you"/"AI") makes responses feel more natural and lets the model reference the user
directly in its answers.

### Follow-ups / ideas not yet implemented

- Persist chosen names across sessions (currently re-prompted every run).
- Allow supplying names via CLI flags or environment variables for non-interactive use.

---

## `list_dir` tool

**Implemented:** 2026-08-29
**Status:** Complete
**Files touched:** `harness/builtins.py`, `harness/tools.py`
**Tests:** Full suite (31 passed, no regressions)

### Summary

Added a `list_dir(path)` primitive that lists a directory's entries (sorted, directories
suffixed with `/`), and registered it as the `list_dir` tool with `READ_ONLY` permission and
an optional `path` argument (defaults to `.`). The agent can now enumerate files/subfolders
without shelling out via `bash`.

### Follow-ups / ideas not yet implemented

- Recursive/glob listing option.
- Filtering hidden files or by extension.
