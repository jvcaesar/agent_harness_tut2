
# Agent Harness Tutorial 2
What is an Agent Harness? and How to build a great one!
https://www.youtube.com/watch?v=nWzXyjXCoCE

Building a minimal version of harness with python.
9 components to build an agent harness.

## How to run

Create a virtual environment and install the package with test dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .[dev]
```

Copy the provider template, then configure one model provider in `.env`:

```powershell
Copy-Item .env.example .env
```

To run with Ollama, start Ollama and pull a model, then set these values in `.env`:

```powershell
ollama pull llama3.1
ollama serve
```

```dotenv
OLLAMA_ENABLED=true
OLLAMA_MODEL=llama3.1
```

To run with OpenAI instead, leave `OLLAMA_ENABLED=false` and set:

```dotenv
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
```

The application loads `.env` automatically from the project root. Start the agent harness with:

```powershell
python agent.py
```

The agent prints the selected provider, such as `Active model: OllamaModel (llama3.1)`, then starts an interactive chat. Type `exit`, `bye`, or `quit` to end the session gracefully. Without provider configuration, it uses the offline `DummyModel`.

Ask `What tools do you have?` or `List your tools.` during a chat to have the model invoke the registry-backed `list_tools` tool. The harness exposes `list_tools`, `read_file`, `grep`, `write_file`, `edit_file`, and `bash`, subject to its configured permission level.

### Tool safety

File tools can only access paths inside the harness workspace. Shell commands require `full` permission, run from the workspace directory, and reject recursive deletion, disk-formatting, shutdown, and download-and-execute patterns. Every denial is returned to the model as an explanation, so it can adjust its next action.

### Error handling

The interactive agent translates common provider failures into actionable messages. For example, Ollama connection errors recommend starting `ollama serve`; missing Ollama models recommend the appropriate `ollama pull` command; and OpenAI authentication, timeout, connection, and rate-limit failures explain the next action. A redacted `model_error` event is written to `.harness/session.jsonl` for troubleshooting. Set `HARNESS_DEBUG=true` in `.env` to also display the redacted diagnostic detail in the chat.

Run the test suite with:

```powershell
python -m pytest -q
```

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

### Current status

The harness is implemented and runnable. It includes an offline `DummyModel`, a local
`OllamaModel`, and an `OpenAIModel` selected from environment variables. The example runner,
demo, and tests exercise the same harness loop and tool-dispatch flow.

