
# Agent Harness Tutorial 2
What is an Agent Harness? and How to build a great one!
https://www.youtube.com/watch?v=nWzXyjXCoCE

Building a minimal version of harness with python.
9 components to build an agent harness.

## Project structure

```text
build/
    harness/            # the package
        __init__.py
        loop.py             # 01 while loop
        context.py          # 02 context management
        tools.py            # 03 skills & tools registry
        subagents.py        # 04 sub-agent archetypes
        builtins.py         # 05 built-in primitives
        persistence.py      # 06 JSONL session
        prompt.py           # 07 System prompt assembly
        hooks.py            # 08 pre/post hooks
        permissions.py      # 09 permissions and safety
        model.py
    demo/               # target project
        agent.md            # 
        claude.md           # picked up by component 07
        main.py             # the file the agent edits
        test_main.py
        run_demo.py         # end-to-end runner
    tests/
        test_harness.py     # validates every component
```
---

## What this project is expected to accomplish

This is a **work-in-progress scaffold** for building a minimal-but-real **agent harness** in
Python. It follows the tutorial "What is an Agent Harness? And how to build a great one!"
(<https://www.youtube.com/watch?v=nWzXyjXCoCE>) and breaks an agent harness down into nine
components that are intended to be developed one at a time.

An agent harness is the plumbing that sits between an LLM and the world. It gives the model a
reliable loop in which to (1) look at the goal and conversation history, (2) call a tool, and
(3) observe the resulting feedback, repeating until the turn ends or the run budget is spent.
Around that core, the harness provides context management, a tool registry, built-in
primitives, permission and safety checks, hook-based extensibility, an audit trail, a system
prompt assembler, and reusable sub-agent archetypes.

### Intended end state (roadmap)

When all of the stubs are completed, this project should be able to:

1. **Run a goal-driven loop** (`loop.py`) - the only file that talks to the model. It drives
   the `decide -> dispatch -> feedback` cycle and terminates on an `end_turn` response or after
   `max_iterations`.
2. **Expose a tool registry** (`tools.py`) - maps tool `name -> permission -> handler` and
   produces machine-readable tool descriptors for the model.
3. **Provide five primitives** (`builtins.py`) - the non-negotiable `read_file`, `write_file`,
   `edit_file`, `bash`, and `grep`.
4. **Manage context** (`context.py`) - compact the message history when it grows past a
   threshold, keeping the most recent turns.
5. **Persist sessions** (`persistence.py`) - append-only JSONL event log, flushed on every
   write, replayable for auditing and experiments.
6. **Assemble the system prompt** (`prompt.py`) - combine a static scaffold with any instruction
   files (AGENTS.md / CLAUDE.md) discovered by walking parent directories.
7. **Harden every tool call** (`hooks.py`) - pre-hooks can allow or deny a dispatch, post-hooks
   audit or log the outcome.
8. **Enforce permissions** (`permissions.py`) - a three-tier model (`read` < `workspace` <
   `full`) that also classifies bash commands and gates dangerous ones.
9. **Spawn sub-agents** (`subagents.py`) - three preset archetypes: `explore` (read-only recon),
   `general` (default workspace agent), and `verify` (runs tests to confirm changes).
10. **Demonstrate end-to-end** with the planned `demo/` target project (the agent edits
    `main.py`, confirms with `test_main.py`, orchestrated by `run_demo.py`) plus a
    `tests/test_harness.py` suite that validates every component. An optional `model.py`
    wrapper is expected to hold the LLM client.

### Current status: stubs, not runnable yet

The project is currently a **scaffold of stubs**. Each module sketches the shape and intent of
its component, but many pieces are incomplete, missing, or intentionally rough, so the harness
cannot run end-to-end yet:

- `loop.py` - the main loop body is outlined, but there is **no enclosing harness class**; it
  references `self.context`, `self.model`, `self.tools`, `self._dispatch_tool`, and
  `self.max_iterations`, none of which are defined anywhere.
- `context.py` - compaction logic calls `_summarize(...)`, which is **not implemented**, and it
  imports `dataclass` from `attr` instead of the standard library `dataclasses`.
- `tools.py` - the registry itself is close to complete, but the skill layer (tools composed
  from other tools, resolved via markdown files) is not implemented.
- `subagents.py` - the presets reference `SubAgentSpec` and `Permission`, neither of which is
  imported; the constant names would also need to match `permissions.py` (`READ_ONLY`, not
  `READONLY`).
- `builtins.py` - all five primitives are defined correctly, but `Path` is imported from
  `zipfile` (line 1) rather than `pathlib`, which fails at import time.
- `persistence.py` - append/replay logic is written, but `json` is imported from `streamlit`
  (line 7) instead of the stdlib, introducing an unnecessary third-party dependency.
- `prompt.py` - `assemble_system_prompt` depends on `STATIC_SCAFFOLD`, `INSTRUCTION_FILES`, and
  `_walk_ancestors`, none of which are defined in the file yet.
- `hooks.py` and `permissions.py` are the most complete, self-contained modules.

The `demo/` and `tests/` directories exist but are **empty**, and the `harness` package has no
`__init__.py` or `model.py` yet. The "project structure" sketch above represents the target
layout; the immediate work is the `harness/` package itself. Note that the current tree sits at
the project root rather than under a `build/` folder - either move the package into `build/`
when the demo runner is wired, or update the structure diagram to match the simpler layout.

