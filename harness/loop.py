# A component of the harness that runs a loop until a goal is achieved.
# decide, dispatch, feedback, terminate
# the only file that calls the model
# this is the entire engine of the harness, it is responsible for running the loop until the goal is achieved.

from pathlib import Path

from harness.context import ContextManager
from harness.hooks import HookContext, Hooks
from harness.permissions import Permission, can_dispatch
from harness.persistence import SessionPersistence
from harness.prompt import assemble_system_prompt
from harness.tools import ToolRegistry, register_core_tools


class Harness:
    def __init__(
        self,
        model,
        cwd: str | Path | None = None,
        max_iterations: int = 10,
        context: ContextManager | None = None,
        tools: ToolRegistry | None = None,
        hooks: Hooks | None = None,
        persistence: SessionPersistence | None = None,
        permission: str = Permission.WORKSPACE,
    ) -> None:
        self.model = model
        self.cwd = Path(cwd or ".").resolve()
        self.max_iterations = max_iterations
        self.context = context or ContextManager()
        self.tools = tools or register_core_tools(ToolRegistry())
        self.hooks = hooks or Hooks()
        self.persistence = persistence or SessionPersistence(self.cwd / ".harness" / "session.jsonl")
        self.permission = permission

    def run(self, goal: str) -> str:
        """
        Run the loop until the goal is achieved.

        Args:
            goal (str): The goal to achieve.

        Returns:
            str: The result of the loop.
        """
        system_prompt = assemble_system_prompt(self.cwd)
        messages = [{"role": "user", "content": goal}]
        result = ""

        for _ in range(1, self.max_iterations + 1):
            messages = self.context.compact_if_needed(messages)
            response = self.model(system_prompt, messages, self.tools.descriptors())

            if response.get("stop_reason") == "end_turn":
                return response.get("text", "")

            tool_call = response.get("tool_call") or {}
            result = self._dispatch_tool(tool_call)
            messages.append({"role": "user", "content": f"tool_result: {result}"})

        return f"(Stopped after {self.max_iterations} iterations) {result}"

    def _dispatch_tool(self, tool_call: dict) -> str:
        if not isinstance(tool_call, dict):
            return "Malformed tool call"

        name = str(tool_call.get("name", ""))
        arguments = tool_call.get("arguments") or {}
        if not isinstance(arguments, dict):
            arguments = {}

        tool = self.tools.get_tool(name)
        if tool is None:
            return f"Unknown tool: {name}"

        if not can_dispatch(tool.permission, self.permission):
            return f"Permission denied: {name} requires {tool.permission} but current level is {self.permission}"

        hook_context = HookContext(tool_name=name, tool_input=arguments)
        if self.hooks.fire_pre(hook_context) == "deny":
            return f"Permission denied: {name} blocked by pre-hook"

        try:
            output = tool.handler(arguments)
        except Exception as exc:  # pragma: no cover - defensive path
            output = f"Tool execution failed: {exc}"

        hook_context.tool_output = output
        self.hooks.fire_post(hook_context)
        self.persistence.append_event({
            "event": "tool_call",
            "tool": name,
            "arguments": arguments,
            "result": str(output),
        })
        return str(output)
